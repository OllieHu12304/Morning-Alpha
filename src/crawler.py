"""保留舊 crawler 指令，實際工作交由 TechNews adapter。"""

from technews_adapter import (
    fetch_homepage,
    main,
    parse_articles,
    print_articles,
)


if __name__ == "__main__":
    main()
