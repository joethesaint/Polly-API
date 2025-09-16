import requests
from typing import Optional, List, Dict, Any


def register_user(username: str, password: str, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Register a new user via the /register endpoint.
    
    Args:
        username (str): The username for the new user
        password (str): The password for the new user
        base_url (str): The base URL of the API (default: http://localhost:8000)
    
    Returns:
        Dict[str, Any]: The response containing user information (id, username)
        
    Raises:
        requests.exceptions.RequestException: If the request fails
        ValueError: If the username is already registered (400 status)
    """
    url = f"{base_url}/register"
    
    payload = {
        "username": username,
        "password": password
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            raise ValueError("Username already registered")
        else:
            response.raise_for_status()
            
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"Failed to register user: {e}")


def fetch_polls(skip: Optional[int] = None, limit: Optional[int] = None, 
                base_url: str = "http://localhost:8000") -> List[Dict[str, Any]]:
    """
    Fetch paginated poll data from /polls endpoint.
    
    Args:
        skip (Optional[int]): Number of items to skip for pagination
        limit (Optional[int]): Maximum number of items to return
        base_url (str): The base URL of the API (default: http://localhost:8000)
    
    Returns:
        List[Dict[str, Any]]: List of polls with their details including:
            - id (int): Poll ID
            - question (str): Poll question
            - created_at (str): Creation timestamp
            - owner_id (int): ID of the poll owner
            - options (List[Dict]): List of poll options with id, text, and poll_id
        
    Raises:
        requests.exceptions.RequestException: If the request fails
    """
    url = f"{base_url}/polls"
    
    # Build query parameters
    params = {}
    if skip is not None:
        params["skip"] = skip
    if limit is not None:
        params["limit"] = limit
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
            
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"Failed to fetch polls: {e}")


def cast_vote(poll_id: int, option_id: int, access_token: str, 
              base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Cast a vote on an existing poll.
    
    Args:
        poll_id (int): The ID of the poll to vote on
        option_id (int): The ID of the option to vote for
        access_token (str): JWT access token for authentication
        base_url (str): The base URL of the API (default: http://localhost:8000)
    
    Returns:
        Dict[str, Any]: The vote response containing:
            - id (int): Vote ID
            - user_id (int): ID of the user who voted
            - option_id (int): ID of the selected option
            - created_at (str): Vote timestamp
        
    Raises:
        requests.exceptions.RequestException: If the request fails
        ValueError: If unauthorized (401) or poll/option not found (404)
    """
    url = f"{base_url}/polls/{poll_id}/vote"
    
    payload = {
        "option_id": option_id
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise ValueError("Unauthorized - invalid or missing access token")
        elif response.status_code == 404:
            raise ValueError("Poll or option not found")
        else:
            response.raise_for_status()
            
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"Failed to cast vote: {e}")


def get_poll_results(poll_id: int, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Retrieve poll results for a specific poll.
    
    Args:
        poll_id (int): The ID of the poll to get results for
        base_url (str): The base URL of the API (default: http://localhost:8000)
    
    Returns:
        Dict[str, Any]: The poll results containing:
            - poll_id (int): ID of the poll
            - question (str): The poll question
            - results (List[Dict]): List of results with:
                - option_id (int): Option ID
                - text (str): Option text
                - vote_count (int): Number of votes for this option
        
    Raises:
        requests.exceptions.RequestException: If the request fails
        ValueError: If poll not found (404)
    """
    url = f"{base_url}/polls/{poll_id}/results"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise ValueError("Poll not found")
        else:
            response.raise_for_status()
            
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"Failed to get poll results: {e}")


# Example usage:
if __name__ == "__main__":
    # Example: Register a new user
    try:
        user_data = register_user("testuser", "testpassword")
        print(f"User registered successfully: {user_data}")
    except ValueError as e:
        print(f"Registration failed: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    
    # Example: Fetch polls with pagination
    try:
        polls = fetch_polls(skip=0, limit=10)
        print(f"Fetched {len(polls)} polls")
        for poll in polls:
            print(f"Poll {poll['id']}: {poll['question']}")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    
    # Example: Cast a vote (requires authentication)
    try:
        # Assuming you have an access token from login
        access_token = "your_jwt_token_here"
        vote_data = cast_vote(poll_id=1, option_id=1, access_token=access_token)
        print(f"Vote cast successfully: {vote_data}")
    except ValueError as e:
        print(f"Vote failed: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    
    # Example: Get poll results
    try:
        results = get_poll_results(poll_id=1)
        print(f"Poll results: {results['question']}")
        for result in results['results']:
            print(f"  {result['text']}: {result['vote_count']} votes")
    except ValueError as e:
        print(f"Failed to get results: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")