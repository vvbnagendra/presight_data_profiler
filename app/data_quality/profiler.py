# Pandas Profiling wrapper

from ydata_profiling import ProfileReport

def generate_profile(df):
    return ProfileReport(df, explorative=True)
