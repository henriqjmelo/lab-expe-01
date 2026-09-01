from src.github_client import run_query

TEST_QUERY = """
query {
  viewer {
    login
  }
  rateLimit {
    limit
    remaining
    resetAt
  }
}
"""


def main():
    data = run_query(TEST_QUERY)
    print(f"Autenticado como: {data['viewer']['login']}")
    print(
        f"Rate limit: {data['rateLimit']['remaining']}/{data['rateLimit']['limit']} "
        f"(reset em {data['rateLimit']['resetAt']})"
    )


if __name__ == "__main__":
    main()
