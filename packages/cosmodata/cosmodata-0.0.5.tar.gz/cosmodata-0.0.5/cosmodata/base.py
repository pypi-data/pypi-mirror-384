"""Base functionality of cosmodata"""


def acquire_data(
    src,
    cache_key=None,
    *,
    getter=None,
    refresh=False,
    cache_dir=None,
):
    """
    Acquire data from source with automatic caching (Colab-aware).

    Intelligently caches to Google Drive in Colab or local disk otherwise.
    Auto-detects appropriate getter for URLs and files.

    Args:
        src: Source (URL, filepath, or anything getter can process)
        getter: Function(src) -> data. If None, auto-detects (graze/tabled/requests)
        cache_key: Cache identifier. If None, generates hash from src
        refresh: If True, bypass cache and re-fetch data
        cache_dir: Cache directory. If None, uses Drive in Colab or ~/.data_cache locally

    Returns:
        The acquired data

    Examples:
        # Simple URL to DataFrame (auto-cached)
        df = acquire_data('https://example.com/data.csv')

        # Custom getter with named cache
        data = acquire_data(
            'https://api.example.com/data',
            getter=lambda url: requests.get(url).json(),
            cache_key='api_data'
        )

        # Force refresh cached data
        df = acquire_data(url, refresh=True)
    """
    import os
    import pickle
    from pathlib import Path
    from hashlib import md5

    # Detect Colab and setup cache directory
    try:
        # Note: Don't install locally - it doesn't work outside colab
        import google.colab
        from google.colab import drive

        if cache_dir is None:
            drive_path = '/content/drive'
            if not os.path.exists(f'{drive_path}/MyDrive'):
                print("Mounting Google Drive...")
                drive.mount(drive_path)
            cache_dir = f'{drive_path}/MyDrive/.colab_cache'
    except ImportError:
        # Local execution (not in Colab)
        if cache_dir is None:
            cache_dir = os.path.expanduser('~/.local/share/cosmodata/datasets')

    # Ensure directory exists (needed for both Colab and local)
    os.makedirs(cache_dir, exist_ok=True)
    # Setup cache
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Generate cache key
    if cache_key is None:
        cache_key = md5(str(src).encode()).hexdigest()[:16]

    cache_file = cache_dir / f'{cache_key}.pkl'

    # Try cache first (unless refresh requested)
    if not refresh and cache_file.exists():
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Cache read failed: {e}, fetching fresh data...")

    # Auto-detect getter if not provided
    if getter is None:
        is_url = isinstance(src, str) and src.startswith(('http://', 'https://'))

        # For URLs: try graze > get_table > requests
        if is_url:
            try:
                from graze import graze as _graze

                # Graze already caches, but we cache its output for Colab persistence
                getter = _graze
            except ImportError:
                try:
                    from tabled import get_table

                    getter = get_table
                except ImportError:
                    import requests

                    getter = lambda u: requests.get(u).content
        else:
            # For files/other: try get_table
            try:
                from tabled import get_table

                getter = get_table
            except ImportError:
                raise ValueError("Install tabled or provide a getter function")

    # Fetch data
    print(f"Fetching data from {src}...")
    data = getter(src)

    # Cache the result
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
        print(f"Data cached at: {cache_file}")
    except Exception as e:
        print(f"Warning: Could not cache data: {e}")

    return data
