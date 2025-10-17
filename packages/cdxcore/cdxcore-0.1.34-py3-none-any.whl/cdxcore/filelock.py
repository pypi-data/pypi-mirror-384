# -*- coding: utf-8 -*-
"""
Simple file-based system-wide lock for both 
`Linux <https://code.activestate.com/recipes/519626-simple-file-based-mutex-for-very-basic-ipc/>`__ and 
`Windows <https://timgolden.me.uk/pywin32-docs/Windows_NT_Files_.2d.2d_Locking.html>`__.

Overview
--------

The most effective method of using ``filelock`` is calling :func:`cdxcore.filelock.AttemptLock`
in a context block::
        
    from cdxcore.filelock import FileLock
    from cdxcore.subdir import SubDir
    lock_dir  = SubDir("!/locks",ext="lck")
    lock_name = lock_dir.full_file_name("lock1")
    
    with AcquireLock( lock_name, timeout_second=2, timeout_retry=3 ):
        # do locked activity

    # locked section over

In above example the function :func:`cdxcore.filelock.AcquireLock` will attempt to acquire a file lock using the file ``lock_name`` in three attempts
with a timeout of two seconds between them. If acquiring a lock fails, a :class:`BlockingIOError` is raised.

If successful, the ``with`` construct ensures that the lock is released at the end of the block.

If we can handle a situation where a lock is not acquired safely,
the following pattern  using :func:`cdxcore.filelock.AttemptLock` can bs used::

    from cdxcore.filelock import FileLock
    from cdxcore.subdir import SubDir
    lock_dir  = SubDir("!/locks",ext="lck")
    lock_name = lock_dir.full_file_name("lock1")
    
    with AttemptLock( lock_name, timeout_second=2, timeout_retry=3 ) as lock:
        if lock.acquired:
            # do locked activity
        else:
            # not locked activity
            
    # locked section over

**Multiple Acquisitions**

Im both patterns above the lock was acquired only once. If the lock is to be acquired several times,
or to be passed to other functions, it is better to first create a :class:`cdxcore.filelock.Flock` object
and then use :func:`cdxcore.filelock.FLock.acquire` instead of :func:`cdxcore.filelock.AcquireLock`::
    
    from cdxcore.filelock import FileLock
    from cdxcore.subdir import SubDir

    def subroutine( lock ):
        with lock.aquire( timeout_second=2, timeout_retry=3 ):
            # do locked activity

    def mainroutine():
        lock_dir  = SubDir("!/locks",ext="lck")
        lock_name = lock_dir.full_file_name("lock1")
        lock      = FileLock(lock_name)
    
        with lock.aquire( timeout_second=2, timeout_retry=3 ):
            # do locked activity

        subroutine( lock )
        
In this case, :func:`cdxcore.filelock.FLock.attempt` can be used for conditional workflows
based on lock status::

    def subroutine( lock ):
        with lock.attempt( lock_name, timeout_second=2, timeout_retry=3 ) as lh:
            if not lh.acquired:
                return # job already done
            # do locked activity
        
**Explicit State Management**

The use of ``with`` context blocks ensures that locks are released as soon 
as the protected activity is finished. In some cases we may desired to finely
control such workflow. 
In this case, use :func:`cdxcore.filelock.FLock.acquire` and :func:`cdxcore.filelock.FLock.release`
in pairs::
    
    from cdxcore.filelock import FileLock
    from cdxcore.subdir import SubDir

    lock_dir  = SubDir("!/locks",ext="lck")
    lock_name = lock_dir.full_file_name("lock1")
    lock      = FileLock(lock_name)
    
    def subroutine( lock ):
        if not lock.acquire( timeout_second=2, timeout_retry=3 ):
            return
        # do protected work
        lock.release()
    
    try:    
        if lock.acquire( timeout_second=2, timeout_retry=3 ):
            # do some protected work
            lock.release()
        
        ...
        
        subroutine(lock)
        ...

        if lock.acquire( timeout_second=2, timeout_retry=3 ):
            # do some protected work
            lock.release()

    finally:
        lock.clear() # <- clears all acquisitions of the lock and stops further use.            
        
**Garbage Collection**

By default locks will delete the underlying file using :meth:`cdxcore.filelock.FLock.clear`
upon garbage collection. This can be triggered with :func:`gc.collect`.

Import
------
.. code-block:: python

    from cdxcore.filelock import FileLock, AcquireLock
    
Documentation
-------------
"""

from .err import verify
from .verbose import Context
from .util import datetime, fmt_datetime, fmt_seconds
from .subdir import SubDir

import os
import os.path
import time
import platform as platform
import threading as threading

_IS_WINDOWS  = platform.system()[0] == "W"
_SYSTEM      = "Windows" if _IS_WINDOWS else "Linux"

if _IS_WINDOWS:
    # http://timgolden.me.uk/pywin32-docs/Windows_NT_Files_.2d.2d_Locking.html
    # need to install pywin32
    try:
        import win32file as win32file
    except Exception as e:
        raise ModuleNotFoundError("pywin32") from e

    import win32con
    import pywintypes
    import win32security
    _WIN_HIGHBITS=0xffff0000 #high-order 32 bits of byte range to lock

else:
    win32file = None

import os

class FLock:
    pass

class LockContext(object):
    """
    A context handler returned by :meth:`cdxcore.filelock.Flock.acquire`,
    :meth:`cdxcore.filelock.AcquireLock`, and :meth:`cdxcore.filelock.AttemptLock`.
    """
    def __init__(self, flock : FLock, acquired : bool):
        self._flock    = flock
        self._acquired = acquired
    def __str__(self) -> str:
        return str(self._flock)
    def __bool__(self) -> bool:
        return self._acquired
    @property
    def acquired(self) -> bool:
        """
        Whether the underlying file lock was acquired by this context handler.
        This is might be ``False`` for ``LockContext`` objects
        returned by :meth:`cdxcore.filelock.AttemptLock`
        """
        return self._acquired
    @property
    def filename(self) -> str:
        """ Underlying file lock name """
        return self._flock.filename
    def __enter__(self):
        """
        Enter a context block. This assumes that the lock was aquired; the corresponding ``__exit__``
        will ``release()`` the lock.
        """
        return self
    def __exit__(self, *kargs, **kwargs):
        """ Release the lock """
        if self._acquired:
            self._flock.release()
        return False # raise exceptions
   
class FLock(object):#NOQA
    r"""
    System-wide file lock.
    
    Do not construct members of this class directly as it will not be able to create a second lock on the same
    lock file within the same process. Use the "factory" function  :func:`cdxcore.filelock.FileLock`
    instead.
    """

    _CLASS_LOCK = threading.RLock()
    _LOCKS = {}
    _LOCK_CNT = 0
    
    @staticmethod
    def _create(  filename        : str, * ,
                  release_on_exit : bool = True,
                  verbose         : Context|None = None ):
        """
        Creates a new ``FLock`` in a multi-thread-safe way.
        """
        
        with FLock._CLASS_LOCK:
            flock = FLock._LOCKS.get(filename, None)
            if flock is None:
                flock = FLock( filename=filename, release_on_exit=release_on_exit, verbose=verbose )
                FLock._LOCKS[filename] = flock
            return flock
        
    def __init__(self, filename        : str, * ,
                       release_on_exit : bool = True,
                       verbose         : Context|None = None ):
        """
        __init__
        """
        self._rlock           = threading.RLock()
        self._filename        = SubDir.expandStandardRoot(filename)
        self._fd              = None
        self._pid             = os.getpid()
        self._cnt             = 0
        self._verbose         = verbose if not verbose is None else Context.quiet
        self._release_on_exit = release_on_exit
        nowstr                = fmt_datetime(datetime.datetime.now())
        self._lid             = f"LOCK<{nowstr},...>: {filename}"
        with self._CLASS_LOCK:
            verify( not filename in self._LOCKS, lambda : f"Ther is already a lock for '{filename}' in place. Use 'FileLock()' to share locks accross threads", exception=FileExistsError)
            my_cnt = self._LOCK_CNT
            self._LOCK_CNT += 1
            self._LOCKS[filename] = self            
        self._lid            = f"LOCK<{nowstr},{my_cnt}>: {filename}"

    def __del__(self):#NOQA
        self.clear()
        
    def clear(self):
        """
        Clears the current object and forces its release.        
        Will delete the underlying lock file if ``release_on_exit`` was used
        when constructing the lock.
        """
        with self._rlock:
            if self._filename is None:
                return
            if self._release_on_exit and not self._fd is None:
                self._verbose.write("%s: deleting locked object", self._lid)
                self.release( force=True )
            with self._CLASS_LOCK:
                del self._LOCKS[self._filename]        
            self._filename = None

    def __str__(self) -> str:
        """ Returns the current file name and the number of locks onbtained. """
        assert not self._filename is None, ("Lock has been cleared", self._lid )
        return f"{self._filename}:{self._cnt}"

    def __bool__(self) -> bool:
        """ Whether the lock is held """
        assert not self._filename is None, ("Lock has been cleared", self._lid )
        return self.locked
    @property
    def num_acquisitions(self) -> int:
        """
        Returns the net number of times the file was acquired using :meth:`cdxcore.filelock.FLock.acquire`.
        Zero if the lock is not currently held.
        """
        assert not self._filename is None, ("Lock has been cleared", self._lid )
        return self._cnt
    @property
    def locked(self) -> bool:
        """ Whether the lock is active. """
        assert not self._filename is None, ("Lock has been cleared", self._lid )
        return self._cnt > 0
    @property
    def filename(self) -> str:
        """ Return the filename of the lock. """
        assert not self._filename is None, ("Lock has been cleared", self._lid )
        return self._filename

    def acquire(self,    wait            : bool = True,
                      *, timeout_seconds : int = 1,
                         timeout_retry   : int = 5,
                         raise_on_fail   : bool = True) -> LockContext|None:
        """
        Acquire lock.
        
        If successful, this function returns a :class:`cdxcore.filelock.LockContext` which can
        be used in a ``with`` statement as follows::

            from cdxcore.filelock import FileLock
            from cdxcore.subdir import SubDir
            
            lock_dir  = SubDir("!/locks",ext="lck")
            lock_name = lock_dir.full_file_name("lock1")
            lock      = FileLock(lock_name)
        
            with lock.aquire( timeout_second=2, timeout_retry=3 ):
                # do locked activity
            # no longer locked
            
        In case ``acquire()`` fails to obtain the lock, by default it will raise an exception.

        **One-Shot**
        
        If you only acquire a lock once, it is more convenient to use :func:`cdxcore.filelock.AcquireLock`::
        
            from cdxcore.filelock import FileLock
            from cdxcore.subdir import SubDir
            
            lock_dir  = SubDir("!/locks",ext="lck")
            lock_name = lock_dir.full_file_name("lock1")

            with AcquireLock( lock_name, timeout_second=2, timeout_retry=3 ):
                # do locked activity
            # no longer locked


        Parameters
        ----------
        wait : bool, default ``True``
        
            * If ``False``, return immediately if the lock cannot be acquired.             
            * If ``True``, wait with below parameters; in particular if these are left as defaults the lock will wait indefinitely.
            
        timeout_seconds : int | None, default ``None``
            Number of seconds to wait before retrying.
            Set to ``0``` to fail immediately.
            If set to ``None``, then behaviour will depend on ``wait``:
                
            * If wait is ``True``, then ``timeout_seconds==1``.
            * If wait is ``False``, then ``timeout_seconds==0``.

        timeout_retry : int | None, default ``None``        
            How many times to retry before timing out.
            Set to ``None`` to retry indefinitely.

        raise_on_fail : bool, default ``True``
            By default, if the constructor fails to obtain the lock, raise an exception.
            This will be either of type
            
            * :class:`TimeoutError` if ``timeout_seconds > 0`` and ``wait==True``, or
            * :class:`BlockingIOError` if ``timeout_seconds == 0`` or ``wait==False``.
            
            If the function could not acquire a lock on the file and if ``raise_on_fail`` is ``False``,
            then this function returns ``None``. This can be used for manual control workflows.

        Returns
        -------
            Context : :class:`cdxcore.filelock.LockContext`
                A context manager representing the acquired state which can be used with ``with``. If the context
                manager protocol os used,
                then :meth:`cdxcore.filelock.release` is called at the end of the ``with`` statement.
                
                This function returns ``None`` if the lock could be acquired and ``raise_on_fail`` is ``False``.-heut3//..X
                The method :meth:`cdxcore.filelock.FLock.attempt`
                will return an unacquired context manager in case of a failure.

        Raises
        ------
            Timeout : :class:`TimeoutError`
                Raised if ``acquire`` is ``True``, if ``timeout_seconds > 0`` and ``wait==True``, and if the call failed
                to obtain the file lock.
    
            Blocked : :class:`BlockingIOError`
                Raised if ``acquire`` is ``True``, if ``timeout_seconds == 0`` or ``wait==False``, and if the call failed
                to obtain the file lock.
        """
        
        timeout_seconds = int(timeout_seconds) if not timeout_seconds is None else None
        timeout_retry   = int(timeout_retry) if not timeout_retry is None else None
        assert not self._filename is None, ("self._filename is None. That probably means 'self' was deleted.")

        if timeout_seconds is None:
            timeout_seconds  = 0 if not wait else 1
        else:
            verify( timeout_seconds>=0, "'timeout_seconds' cannot be negative", exception=ValueError)
            verify( not wait or timeout_seconds>0, "Using 'timeout_seconds==0' and 'wait=True' is inconsistent.", exception=ValueError)

        with self._rlock:
            if not self._fd is None:
                self._cnt += 1
                self._verbose.write("%s: acquire(): raised lock counter to %ld", self._lid, self._cnt)
                return LockContext(self,True)
            assert self._cnt == 0
            self._cnt = 0
    
            i = 0
            while True:
                self._verbose.write("\r%s: acquire(): locking [%s]... ", self._lid, _SYSTEM, end='')
                if not _IS_WINDOWS:
                    # Linux
                    # -----
                    # Systemwide Lock (Mutex) using files
                    # https://code.activestate.com/recipes/519626-simple-file-based-mutex-for-very-basic-ipc/
                    try:
                        self._fd = os.open(self._filename, os.O_CREAT|os.O_EXCL|os.O_RDWR)
                        os.write(self._fd, bytes("%d" % self._pid, 'utf-8'))
                    except OSError as e:
                        if not self._fd is None:
                            os.close(self._fd)
                        self._fd  = None
                        if e.errno != 17:
                            self._verbose.write("failed: %s", str(e), head=False)
                            raise e
                else:
                    # Windows
                    # ------
                    secur_att = win32security.SECURITY_ATTRIBUTES()
                    secur_att.Initialize()
                    try:
                        self._fd = win32file.CreateFile( self._filename,
                            win32con.GENERIC_READ|win32con.GENERIC_WRITE,
                            win32con.FILE_SHARE_READ|win32con.FILE_SHARE_WRITE,
                            secur_att,
                            win32con.OPEN_ALWAYS,
                            win32con.FILE_ATTRIBUTE_NORMAL , 0 )
    
                        ov=pywintypes.OVERLAPPED() #used to indicate starting region to lock
                        win32file.LockFileEx(self._fd,win32con.LOCKFILE_EXCLUSIVE_LOCK|win32con.LOCKFILE_FAIL_IMMEDIATELY,0,_WIN_HIGHBITS,ov)
                    except BaseException as e:
                        if not self._fd is None:
                            self._fd.Close()
                        self._fd  = None
                        if e.winerror not in [17,33]:
                            self._verbose.write("failed: %s", str(e), head=False)
                            raise e
    
                if not self._fd is None:
                    # success
                    self._cnt = 1
                    self._verbose.write("done; lock counter set to 1", head=False)
                    return LockContext(self,True)
    
                if timeout_seconds <= 0:
                    break
    
                if not timeout_retry is None:
                    i += 1
                    if i>timeout_retry:
                        break
                    self._verbose.write("locked; waiting %s retry %ld/%ld", fmt_seconds(timeout_seconds), i+1, timeout_retry, head=False)
                else:
                    self._verbose.write("locked; waiting %s", fmt_seconds(timeout_seconds), head=False)
    
                time.sleep(timeout_seconds)
    
            if timeout_seconds == 0:
                self._verbose.write("failed.", head=False)
                if raise_on_fail: raise BlockingIOError(self._filename)
            else:
                self._verbose.write("timed out. Cannot access lock.", head=False)
                if raise_on_fail: raise TimeoutError(self._filename, dict(timeout_retry=timeout_retry, timeout_seconds=timeout_seconds))
            return None

    def attempt(self,    wait            : bool = True,
                      *, timeout_seconds : int = 1,
                         timeout_retry   : int = 5 ) -> LockContext:
        """
        Attempt to acquire lock.
        
        This function attempts to obtain the file lock within the specified timeout parameters. It will return
        a :class:`cdxcore.filelock.LockContext` whose property 
        :attr:`cdxcore.filelock.LockContext.acquired`
        provides success of this attempt.

        The context object can be used
        using ``with`` as follows:

            from cdxcore.filelock import FileLock
            from cdxcore.subdir import SubDir
            
            lock_dir  = SubDir("!/locks",ext="lck")
            lock_name = lock_dir.full_file_name("lock1")
            lock      = FileLock(lock_name)
        
            with lock.attempt( timeout_second=2, timeout_retry=3 ) as lh:
                if lh.acquired:
                    # do locked activity
                else:
                    # do some other activity; warn the user; etc
                    
            # no longer locked

        In contrast, the function :meth:`cdxcore.filelock.FLock.acquire` will only return a :class:`cdxcore.filelock.LockContext`
        object if the acquisiton of the lock was successful.
        
        **One-Shot**
        
        If you only make one attempt to use a lock, it is more convenient to use :func:`cdxcore.filelock.AttemptLock`::
        
            with AttemptLock( lock_name, timeout_second=2, timeout_retry=3 ) as lock:
                if lock.acquired:
                    # do locked activity
                else:
                    # do not locked activity
            # no longer locked

        Parameters
        ----------
        wait : bool, default ``True``
        
            * If ``False``, return immediately if the lock cannot be acquired.             
            * If ``True``, wait with below parameters; in particular if these are left as defaults the lock will wait indefinitely.
            
        timeout_seconds : int | None, default ``None``
            Number of seconds to wait before retrying.
            Set to ``0``` to fail immediately.
            If set to ``None``, then behaviour will depend on ``wait``:
                
            * If wait is ``True``, then ``timeout_seconds==1``.
            * If wait is ``False``, then ``timeout_seconds==0``.

        timeout_retry : int | None, default ``None``        
            How many times to retry before timing out.
            Set to ``None`` to retry indefinitely.

        Returns
        -------
            Context : :class:`cdxcore.filelock.LockContext`
                A context representing the acquired state which can be used with ``with``.
                Check :attr:`cdxcore.filelock.LockContext.acquired` to validate whether the lock was acquired successfully. 
                
                If ``with`` is used and :attr:`cdxcore.filelock.LockContext.acquired` is ``True``,
                then :meth:`cdxcore.filelock.release` is called at the end of the ``with`` statement to
                release the acquired lock.
        """
        r = self.acquire( wait=wait, timeout_seconds=timeout_seconds, timeout_retry=timeout_retry, raise_on_fail=False )
        return r if not r is None else LockContext(self, False)

    def release(self, *, force : bool = False ):
        """
        Release lock.
        
        By default this function will only decreased the number of successful acquisitions by one, and will delete the file lock
        only once the number of acquisitions is zero.
        Use ``force`` to force an unlock.

        Parameters
        ----------
            force : bool, default: ``False``
                Whether to close the file regardless of the internal acquisition counter.

        Returns
        -------
            Remaining : int
                Returns numbner of remaining lock acquisitions; in other words returns 0 if the lock is no longer locked by this process.
        """
        with self._rlock:
            # we must have a file handle unless 'force' is used.
            if self._fd is None:
                verify( force, lambda : f"Lock '{self._filename}' is not currrenty locked by this process. Use 'force' to avoid this message if need be.")
                self._cnt = 0
                return 0
            
            # lower counter
            assert self._cnt > 0, "Internal error - have file handle but counter is zero"
            self._cnt -= 1
            if self._cnt > 0 and not force:
                self._verbose.write("%s: lock counter lowered to %ld", self._lid, self._cnt)
                return self._cnt

            # remove file    
            self._verbose.write("%s: releasing lock [%s]... ", self._lid, _SYSTEM, end='')
            err = ""
            if not _IS_WINDOWS:
                # Linux
                # Locks on Linxu are remarably shaky.
                # In particular, it is possible to remove a locked file.
                try:
                    os.close(self._fd)
                except:
                    err = f"*** WARNING: could not close lock file '{self._filename}'."
                    pass
                try:
                    os.remove(self._filename)
                except FileNotFoundError:
                    pass
                except:
                    err = f"*** WARNING: could not delete lock file '{self._filename}'." if err == "" else err
            else:
                try:
                    ov=pywintypes.OVERLAPPED() #used to indicate starting region to lock
                    win32file.UnlockFileEx(self._fd,0,_WIN_HIGHBITS,ov)
                except:
                    err = "*** WARNING: could not unlock lock file '{self._filename}'."
                    pass
                try:
                    self._fd.Close()
                except:
                    err = "*** WARNING: could not close lock file '{self._filename}'." if err == "" else err
                    pass
                try:
                    win32file.DeleteFile(self._filename)
                except FileNotFoundError:
                    pass
                except:
                    err = f"*** WARNING: could not delete lock file '{self._filename}'." if err == "" else err
                    pass
            self._verbose.write("done; lock file deleted." if err=="" else err, head=False)
            self._fd  = None
            self._cnt = 0
            return 0

def FileLock(   filename, * ,
                release_on_exit : bool = True,
                verbose         : Context|None = None ) -> FLock:
    """
    Acquire a file lock object shared among threads.

    This function is useful if a lock is going the be used iteratively, including
    passing it to sub-routines::
    
        from cdxcore.filelock import FileLock
        from cdxcore.subdir import SubDir

        def subroutine( lock ):
            with lock.aquire( lock_name, timeout_second=2, timeout_retry=3 ):
                # do locked activity

        def mainroutine():
            lock_dir  = SubDir("!/locks",ext="lck")
            lock_name = lock_dir.full_file_name("lock1")
            lock      = FileLock(lock_name)
        
            with lock.aquire( timeout_second=2, timeout_retry=3 ):
                # do locked activity

            subroutine( lock )

    If the lock is only used for a one-of acquisition, it is usally
    prettier to use :func:`cdxcore.filelock.AcquireLock` instead.


    Parameters
    ----------
        filename : str
            Filename of the lock.
            
            ``filename`` may start with ``'!/'`` to refer to the temp directory, or ``'~/'`` to refer to the user directory.
            On Unix ``'/dev/shm/'`` can be used to refer to the standard shared memory directory in case a shared memory
            file is being locked.

        release_on_exit : bool, default ``True``
            Whether to auto-release the lock upon exit.
            
        verbose : :class:`cdxcore.verbose.Context` |  None, default ``None``
            Context which will print out operating information of the lock. This is helpful for debugging.
            In particular, it will track ``__del__()`` function calls.
            Set to ``None`` to supress printing any context.

    Returns
    -------
        lock : :class:`cdxcore.filelock.FLock`
            The lock. This function will re-use an existing lock if it has been created elsewhere by the same process.
    """       
    return FLock._create( filename=filename,
                          release_on_exit=release_on_exit,
                          verbose=verbose )

def AttemptLock(filename, * ,
                wait            : bool = True,
                timeout_seconds : int|None = None,
                timeout_retry   : int|None = None,
                verbose         : Context|None = None ) -> FLock:
        """
        Attempt to acquire a file lock and return a context handler even if the lock was not acquired.
        The context handler's :attr:`cdxcore.filelock.LockContext.acquired` can be used to assess
        whether the lock was acquired.
        
        The pattern is as follows::

            from cdxcore.filelock import FileLock
            from cdxcore.subdir import SubDir
            
            lock_dir  = SubDir("!/locks",ext="lck")
            lock_name = lock_dir.full_file_name("lock1")
            
            with AttemptLock( lock_name, timeout_second=2, timeout_retry=3 ) as lock:
                if lock.acquired:
                    # do locked activity
                else:
                    # do not locked activity
            # no longer locked
            
        Parameters
        ----------
        filename : str
            Filename of the lock.
            
            ``filename`` may start with ``'!/'`` to refer to the temp directory, or ``'~/'`` to refer to the user directory.
            On Unix ``'/dev/shm/'`` can be used to refer to the standard shared memory directory in case a shared memory
            file is being locked.

        wait : bool, default ``True``
        
            * If ``False``, return immediately if the lock cannot be acquired.             
            * If ``True``, wait with below parameters; in particular if these are left as defaults the lock will wait indefinitely.
            
        timeout_seconds : int | None, default ``None``
            Number of seconds to wait before retrying.
            Set to ``0``` to fail immediately.
            If set to ``None``, then behaviour will depend on ``wait``:
                
            * If wait is ``True``, then ``timeout_seconds==1``.
            * If wait is ``False``, then ``timeout_seconds==0``.

        timeout_retry : int | None, default ``None``        
            How many times to retry before timing out.
            Set to ``None`` to retry indefinitely.

        verbose : :class:`cdxcore.verbose.Context` |  None, default ``None``
            Context which will print out operating information of the lock. This is helpful for debugging.
            In particular, it will track ``__del__()`` function calls.
            Set to ``None`` to supress printing any context.

        Exceptions
        ----------
            Will not raise any exceptions
                
        Returns
        -------
            Filelock if acquired or None
        """
        flock = FLock._create( filename=filename,
                               release_on_exit=True,
                               verbose=verbose )
        return flock.attempt( wait=wait, timeout_seconds=timeout_seconds, timeout_retry=timeout_retry, raise_on_fail=True )
    
def AcquireLock(filename, * ,
                wait            : bool = True,
                timeout_seconds : int|None = None,
                timeout_retry   : int|None = None,
                verbose         : Context|None = None ) -> LockContext:
        """
        Acquire a file lock and return a context handler, or raise an exception.
        The context handler can be used in a ``with`` statement as follows::

            from cdxcore.filelock import FileLock
            from cdxcore.subdir import SubDir
            
            lock_dir  = SubDir("!/locks",ext="lck")
            lock_name = lock_dir.full_file_name("lock1")
            
            with AcquireLock( lock_name, timeout_second=2, timeout_retry=3 ):
                # do locked activity
            # no longer locked
            
        Note that this function will raise an exception if the lock could be acquired.
        Use :func:`cdxcore.filelock.AttemptLock` to obtain a context handler
        even if the lock was not acquired.

        Parameters
        ----------
        filename : str
            Filename of the lock.
            
            ``filename`` may start with ``'!/'`` to refer to the temp directory, or ``'~/'`` to refer to the user directory.
            On Unix ``'/dev/shm/'`` can be used to refer to the standard shared memory directory in case a shared memory
            file is being locked.

        wait : bool, default ``True``
        
            * If ``False``, return immediately if the lock cannot be acquired.             
            * If ``True``, wait with below parameters; in particular if these are left as defaults the lock will wait indefinitely.
            
        timeout_seconds : int | None, default ``None``
            Number of seconds to wait before retrying.
            Set to ``0``` to fail immediately.
            If set to ``None``, then behaviour will depend on ``wait``:
                
            * If wait is ``True``, then ``timeout_seconds==1``.
            * If wait is ``False``, then ``timeout_seconds==0``.

        timeout_retry : int | None, default ``None``        
            How many times to retry before timing out.
            Set to ``None`` to retry indefinitely.

        verbose : :class:`cdxcore.verbose.Context` |  None, default ``None``
            Context which will print out operating information of the lock. This is helpful for debugging.
            In particular, it will track ``__del__()`` function calls.
            Set to ``None`` to supress printing any context.

        Returns
        -------
            Context : :class:`cdxcore.filelock.LockContext`
                A context representing the acquired state which can be used with ``with``. The function
                :meth:`cdxcore.filelock.release` is called at the end of the ``with`` statement to
                release the acquired lock.

        Raises
        ------
            Timeout : :class:`TimeoutError`
                Raised if ``acquire`` is ``True``, if ``timeout_seconds > 0`` and ``wait==True``, and if the call failed
                to obtain the file lock.
    
            Blocked : :class:`BlockingIOError`
                Raised if ``acquire`` is ``True``, if ``timeout_seconds == 0`` or ``wait==False``, and if the call failed
                to obtain the file lock.
        """
        flock = FLock._create( filename=filename,
                               release_on_exit=True,
                               verbose=verbose )
        return flock.acquire( wait=wait, timeout_seconds=timeout_seconds, timeout_retry=timeout_retry, raise_on_fail=True )
    
