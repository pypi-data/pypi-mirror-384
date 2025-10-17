"""
FastDup Python 2 compatibility stub package.
This package only serves to provide a clear error message for Python 2.
"""
import sys
import platform
import hashlib
import uuid
import os

# Generate token for sentry reporting (same as main package)
token = hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()

def report_to_sentry():
    """Report unsupported Python version to Sentry"""
    try:
        # Check if sentry is disabled
        if os.environ.get("SENTRY_OPT_OUT", "0") == "1":
            return
            
        import sentry_sdk
        
        sentry_sdk.init(
            dsn="https://b526f209751f4bcea856a1d90e7cf891@o4504135122944000.ingest.sentry.io/4504168616427520",
            debug=os.environ.get("SENTRY_DEBUG", "0") == "1",
            traces_sample_rate=1.0,
            release="python2-compatibility-stub",
            default_integrations=False
        )
        
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("section", "python_version_compatibility_check")
            scope.set_tag("python_version", "{}.{}".format(sys.version_info.major, sys.version_info.minor))
            scope.set_tag("python_micro_version", "{}.{}.{}".format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro))
            scope.set_tag("platform", platform.platform())
            scope.set_tag("platform_system", platform.system())
            scope.set_tag("architecture", platform.machine())
            scope.set_tag("token", token)
            scope.set_tag("unit_test", os.environ.get("UNIT_TEST", False))
            scope.set_tag("production", "FASTDUP_PRODUCTION" in os.environ)
            scope.set_tag("python_implementation", platform.python_implementation())
            scope.set_extra("full_python_version", sys.version)
            scope.set_extra("platform_version", platform.version())
            scope.set_extra("python_executable", sys.executable)
            
            message = "FastDup import attempted on unsupported Python {}.{}.{} ({})".format(
                sys.version_info.major, 
                sys.version_info.minor, 
                sys.version_info.micro,
                platform.python_implementation()
            )
            
            sentry_sdk.capture_message(message, level="warning")
        
        sentry_sdk.flush(timeout=5)
        
        if os.environ.get("SENTRY_DEBUG", "0") == "1":
            print("DEBUG: Sentry message sent for Python 2 compatibility check")
            
    except Exception as e:
        if os.environ.get("SENTRY_DEBUG", "0") == "1":
            print("DEBUG: Sentry reporting failed: {}".format(e))
        pass  # Silently fail if sentry reporting fails

# Check Python version and show error message
if sys.version_info.major == 2:
    # Report to Sentry before raising error
    report_to_sentry()
    
    python_version = "{}.{}.{}".format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
    error_msg = """
{}
{}
{}
{}
{}  FastDup requires Python 3.9+                                                {}
{}
{}  Your current Python version: {:<43}{}
{}
{}  Supported platforms:                                                        {}
{}  • Linux x86_64 or ARM64                                                     {}
{}  • macOS Apple Silicon (M1/M2)                                               {}
{}  • Windows WSL2                                                              {}
{}
{}  To use FastDup, please:                                                     {}
{}  1. Install Python 3.9 or higher                                             {}
{}  2. Create a virtual environment with a supported Python version             {}
{}  3. Install fastdup in that environment                                      {}
{}
{}  Example:                                                                    {}
{}    python3.9 -m venv fastdup_env                                             {}
{}    source fastdup_env/bin/activate                                           {}
{}    pip install fastdup                                                       {}
{}
{}  For more information, visit: https://github.com/visualdatabase/fastdup      {}
{}
{}
""".format(
        "╔══════════════════════════════════════════════════════════════════════════════╗",
        "║                           FASTDUP VERSION ERROR                              ║",
        "╠══════════════════════════════════════════════════════════════════════════════╣",
        "║                                                                              ║",
        "║", "║",
        "║                                                                              ║",
        "║", python_version, "║",
        "║                                                                              ║",
        "║", "║",
        "║", "║",
        "║", "║",
        "║", "║",
        "║                                                                              ║",
        "║", "║",
        "║", "║",
        "║", "║",
        "║", "║",
        "║                                                                              ║",
        "║", "║",
        "║", "║",
        "║", "║",
        "║", "║",
        "║                                                                              ║",
        "║", "║",
        "║                                                                              ║",
        "╚══════════════════════════════════════════════════════════════════════════════╝"
    )
    
    raise ImportError(error_msg)

# If we get here, it's not Python 2 (shouldn't happen with this stub)
raise ImportError("This is a Python 2 compatibility stub package. Please install the full FastDup package for your Python version.")