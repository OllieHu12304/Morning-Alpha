"""重新建立 Morning Alpha 新聞與公司的關聯。"""

import pymysql

from news_company_links import run_news_company_sync


def main():
    """執行同步並顯示初學者容易確認的摘要。"""
    try:
        result = run_news_company_sync()
        print(
            "新聞公司關聯更新完成："
            f"分析 {result['news_count']} 則新聞，"
            f"建立 {result['link_count']} 筆關聯。"
        )
        return 0
    except pymysql.MySQLError as error:
        print(f"新聞公司關聯更新失敗：MySQL 錯誤：{error}")
    except ValueError as error:
        print(f"新聞公司關聯更新失敗：設定或資料錯誤：{error}")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
