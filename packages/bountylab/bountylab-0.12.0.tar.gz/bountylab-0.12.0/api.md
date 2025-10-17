# RawUsers

Types:

```python
from bountylab.types import (
    RawUserRetrieveResponse,
    RawUserByLoginResponse,
    RawUserContributesResponse,
    RawUserFollowersResponse,
    RawUserFollowingResponse,
    RawUserOwnsResponse,
    RawUserStarsResponse,
)
```

Methods:

- <code title="get /api/raw/users/{id}">client.raw_users.<a href="./src/bountylab/resources/raw_users.py">retrieve</a>(id) -> <a href="./src/bountylab/types/raw_user_retrieve_response.py">RawUserRetrieveResponse</a></code>
- <code title="post /api/raw/users/by-login">client.raw_users.<a href="./src/bountylab/resources/raw_users.py">by_login</a>(\*\*<a href="src/bountylab/types/raw_user_by_login_params.py">params</a>) -> <a href="./src/bountylab/types/raw_user_by_login_response.py">RawUserByLoginResponse</a></code>
- <code title="get /api/raw/users/{id}/contributes">client.raw_users.<a href="./src/bountylab/resources/raw_users.py">contributes</a>(id, \*\*<a href="src/bountylab/types/raw_user_contributes_params.py">params</a>) -> <a href="./src/bountylab/types/raw_user_contributes_response.py">RawUserContributesResponse</a></code>
- <code title="get /api/raw/users/{id}/followers">client.raw_users.<a href="./src/bountylab/resources/raw_users.py">followers</a>(id, \*\*<a href="src/bountylab/types/raw_user_followers_params.py">params</a>) -> <a href="./src/bountylab/types/raw_user_followers_response.py">RawUserFollowersResponse</a></code>
- <code title="get /api/raw/users/{id}/following">client.raw_users.<a href="./src/bountylab/resources/raw_users.py">following</a>(id, \*\*<a href="src/bountylab/types/raw_user_following_params.py">params</a>) -> <a href="./src/bountylab/types/raw_user_following_response.py">RawUserFollowingResponse</a></code>
- <code title="get /api/raw/users/{id}/owns">client.raw_users.<a href="./src/bountylab/resources/raw_users.py">owns</a>(id, \*\*<a href="src/bountylab/types/raw_user_owns_params.py">params</a>) -> <a href="./src/bountylab/types/raw_user_owns_response.py">RawUserOwnsResponse</a></code>
- <code title="get /api/raw/users/{id}/stars">client.raw_users.<a href="./src/bountylab/resources/raw_users.py">stars</a>(id, \*\*<a href="src/bountylab/types/raw_user_stars_params.py">params</a>) -> <a href="./src/bountylab/types/raw_user_stars_response.py">RawUserStarsResponse</a></code>

# RawRepos

Types:

```python
from bountylab.types import (
    RawRepoRetrieveResponse,
    RawRepoByFullnameResponse,
    RawRepoContributesResponse,
    RawRepoOwnsResponse,
    RawRepoStarsResponse,
)
```

Methods:

- <code title="get /api/raw/repos/{id}">client.raw_repos.<a href="./src/bountylab/resources/raw_repos.py">retrieve</a>(id) -> <a href="./src/bountylab/types/raw_repo_retrieve_response.py">RawRepoRetrieveResponse</a></code>
- <code title="post /api/raw/repos/by-fullname">client.raw_repos.<a href="./src/bountylab/resources/raw_repos.py">by_fullname</a>(\*\*<a href="src/bountylab/types/raw_repo_by_fullname_params.py">params</a>) -> <a href="./src/bountylab/types/raw_repo_by_fullname_response.py">RawRepoByFullnameResponse</a></code>
- <code title="get /api/raw/repos/{id}/contributes">client.raw_repos.<a href="./src/bountylab/resources/raw_repos.py">contributes</a>(id, \*\*<a href="src/bountylab/types/raw_repo_contributes_params.py">params</a>) -> <a href="./src/bountylab/types/raw_repo_contributes_response.py">RawRepoContributesResponse</a></code>
- <code title="get /api/raw/repos/{id}/owns">client.raw_repos.<a href="./src/bountylab/resources/raw_repos.py">owns</a>(id, \*\*<a href="src/bountylab/types/raw_repo_owns_params.py">params</a>) -> <a href="./src/bountylab/types/raw_repo_owns_response.py">RawRepoOwnsResponse</a></code>
- <code title="get /api/raw/repos/{id}/stars">client.raw_repos.<a href="./src/bountylab/resources/raw_repos.py">stars</a>(id, \*\*<a href="src/bountylab/types/raw_repo_stars_params.py">params</a>) -> <a href="./src/bountylab/types/raw_repo_stars_response.py">RawRepoStarsResponse</a></code>

# SearchUsers

Types:

```python
from bountylab.types import SearchUserNaturalLanguageResponse, SearchUserSearchResponse
```

Methods:

- <code title="post /api/search/users/natural-language">client.search_users.<a href="./src/bountylab/resources/search_users.py">natural_language</a>(\*\*<a href="src/bountylab/types/search_user_natural_language_params.py">params</a>) -> <a href="./src/bountylab/types/search_user_natural_language_response.py">SearchUserNaturalLanguageResponse</a></code>
- <code title="post /api/search/users">client.search_users.<a href="./src/bountylab/resources/search_users.py">search</a>(\*\*<a href="src/bountylab/types/search_user_search_params.py">params</a>) -> <a href="./src/bountylab/types/search_user_search_response.py">SearchUserSearchResponse</a></code>

# SearchRepos

Types:

```python
from bountylab.types import SearchRepoNaturalLanguageResponse, SearchRepoSearchResponse
```

Methods:

- <code title="post /api/search/repos/natural-language">client.search_repos.<a href="./src/bountylab/resources/search_repos.py">natural_language</a>(\*\*<a href="src/bountylab/types/search_repo_natural_language_params.py">params</a>) -> <a href="./src/bountylab/types/search_repo_natural_language_response.py">SearchRepoNaturalLanguageResponse</a></code>
- <code title="post /api/search/repos">client.search_repos.<a href="./src/bountylab/resources/search_repos.py">search</a>(\*\*<a href="src/bountylab/types/search_repo_search_params.py">params</a>) -> <a href="./src/bountylab/types/search_repo_search_response.py">SearchRepoSearchResponse</a></code>
