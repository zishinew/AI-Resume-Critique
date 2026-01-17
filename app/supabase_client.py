from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY

# Service role client for admin operations (backend use)
# This client bypasses Row Level Security
supabase_admin: Client = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Anon client (if needed for public operations)
supabase: Client = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def get_supabase_admin() -> Client:
    """Get the Supabase admin client. Raises if not configured."""
    if supabase_admin is None:
        raise RuntimeError("Supabase is not configured. Check environment variables.")
    return supabase_admin


def get_supabase() -> Client:
    """Get the Supabase anon client. Raises if not configured."""
    if supabase is None:
        raise RuntimeError("Supabase is not configured. Check environment variables.")
    return supabase
