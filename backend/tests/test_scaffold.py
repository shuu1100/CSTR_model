"""Phase 0 scaffold and environment verification tests."""

def test_environment_scaffold():
    """Verify that core numerical packages can be imported and are operational."""
    import numpy as np
    import scipy
    import pandas as pd
    
    assert np.__version__ is not None
    assert scipy.__version__ is not None
    assert pd.__version__ is not None
