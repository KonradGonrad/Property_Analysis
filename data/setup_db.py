if __name__ == '__main__':
    import sys
    import os
    import psycopg2

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.append(project_root)

    from house_scrapper.house_scrapper.settings import SCRAP_STATS, SCRAP_NUMBER, SCRAP_PHOTOS, SCRAP_DESCRIPTION
    from database_info import db_name, acc_name, password

    username = acc_name
    db_name = db_name
    password = password


    TABLE_FLAGS = {
        'listing_stats': SCRAP_STATS,
    }

    COLUMN_TAGS = {
        'phone_number': SCRAP_NUMBER,
        'num_photo': SCRAP_PHOTOS,
        'len_description': SCRAP_DESCRIPTION
    }

    with open('data/schema.sql', 'r', encoding='utf-8') as file:
        raw_sql = file.read()

    import re
    blocks = re.split(r"-- CREATE:([a-z_]+)", raw_sql)

    sql_blocks = {}
    for i in range(1, len(blocks), 2):
        name = blocks[i].strip()
        code = blocks[i + 1].strip()

        if name in TABLE_FLAGS and not TABLE_FLAGS[name]:
            continue

        filtered_lines = []
        skip_next_line = False
        for i, line in enumerate(code.splitlines()):
            col_tag_match = re.search(r"-- COL:([a-z_]+)", line)
            if col_tag_match:
                col_name = col_tag_match.group(1) # name after CREATE:{name}
                if col_name in COLUMN_TAGS and not COLUMN_TAGS[col_name]:
                    skip_next_line = True
                    continue
            elif skip_next_line:
                skip_next_line = False
                continue
            else:
                filtered_lines.append(line)

        sql_blocks[name] = "\n".join(filtered_lines)

    # print(sql_blocks['listings'])
    # print(COLUMN_TAGS)


    conn = psycopg2.connect(f"dbname={db_name} user={username} password={password}")
    cur = conn.cursor()

    for table_name, sql_code in sql_blocks.items():
        try:
            print(f"Creating table {table_name}...")
            cur.execute(sql_code)
            conn.commit()
        except Exception as e:
            print(f"Error while creating table {table_name}:", e)
            conn.rollback()
        
    cur.close
    conn.close


