================
pip-system-certs
================

This package automatically configures Python to use system certificates from the OS certificate store instead of the bundled certificates via the ``truststore`` library.

This allows pip and Python applications to verify TLS/SSL connections to servers whose certificates are trusted by your system.

Simply install with::

  pip install pip_system_certs

and Python will automatically use your system's certificate store for all SSL verification.

This works for pip, requests, urllib3, and any other Python library that uses the standard SSL context.

Requirements
------------
* Python 3.10 or higher
* pip 24.2 or higher (upgraded automatically if needed)

Compatibility
-------------
``pip-system-certs`` uses pip's built-in ``truststore`` library to inject system certificate 
verification into Python's SSL context. This provides native OS integration using:

* **macOS**: Security framework
* **Windows**: CryptoAPI  
* **Linux**: OpenSSL with system certificate stores

This approach leverages the same truststore technology that pip uses internally, ensuring 
compatibility and reliability. It automatically works with any Python library that uses SSL 
(requests, urllib3, httpx, etc.).

If you encounter issues, please report them at https://gitlab.com/alelec/pip-system-certs/-/issues

Known Issues
------------
* ``conda`` virtual environments on Linux may install a separate SSL certificate store which 
  takes precedence over the system store, potentially preventing this package from accessing 
  system-installed certificates.

PyInstaller
-----------
The automatic certificate configuration relies on a ``.pth`` file that Python loads at startup. 
This method does not work when bundling applications with PyInstaller or similar tools.

For PyInstaller applications, manually enable system certificates by adding this line early 
in your main script::

    import pip_system_certs.wrapt_requests; pip_system_certs.wrapt_requests.inject_truststore()

This must be called before any SSL connections are made.

Architecture
------------
This package uses a bootstrap system to automatically inject system certificate support:

1. A ``.pth`` file triggers the bootstrap when Python starts
2. Uses pip's vendored ``truststore`` library (pip 24.2+) for compatibility
3. Calls ``truststore.inject_into_ssl()`` to globally configure system certificates
4. All subsequent SSL connections (pip, requests, etc.) use the system certificate store

Acknowledgements
----------------
This package leverages pip's vendored ``truststore`` library by Seth Michael Larson for system 
certificate integration. This ensures compatibility with modern pip versions while avoiding 
dependency conflicts.

The bootstrap system was originally inspired by the autowrapt module.
