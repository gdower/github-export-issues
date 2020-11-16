import requests
import csv
import os

headers = {"Authorization": "Bearer " + os.getenv('BEARER')}

owner = 'SpeciesFileGroup'
project = 'taxonworks'
limit = 100
output = csv.DictWriter(open("issues.tsv", "w"), delimiter='\t', fieldnames=['number', 'state', 'title', 'body', 'author', 'assignees', 'labels', 'createdAt', 'closedAt', 'comments', 'url'])

issues = []


def run_query(query):
    request = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))


cursor = ""
has_next_page = True
while has_next_page:
    query = """
    {{
      repository(owner: "{owner}", name: "{project}") {{
        issues(orderBy: {{field: CREATED_AT, direction: DESC}}, first: {limit}{cursor}) {{
          pageInfo {{
            hasNextPage
            startCursor
            endCursor
          }}
          nodes {{
            number
            title
            body
            state
            url
            labels(first: 100) {{
              nodes {{
                name
              }}
            }}
            createdAt
            closedAt
            author {{
              login
            }}
            assignees(first: 100) {{
              nodes {{
                login
                name
              }}
            }}
            comments {{
              totalCount
            }}
          }}
        }}
      }}
    }}
    """.format(owner=owner, project=project, limit=limit, cursor=cursor)
    results = run_query(query)

    # set pagination cursor
    has_next_page = results['data']['repository']['issues']['pageInfo']['hasNextPage']
    cursor = ", after: \"{cursor}\"".format(cursor=results['data']['repository']['issues']['pageInfo']['endCursor'])
    issues += results['data']['repository']['issues']['nodes']


def format_labels(labels):
    labels_list = []
    for l in labels:
        labels_list.append(l['name'])
    return ', '.join(l for l in labels_list if l != '')


def format_assignees(assignees):
    assignees_list = []
    for a in assignees:
        if a['name'] is None:
            a['name'] = ''
        else:
            a['name'] = '({})'.format(a['name'] )
        assignees_list.append(' '.join(u for u in [a['login'], a['name']] if u != ''))
    return ', '.join(u for u in assignees_list if u != '')


def format_body(body):
    body = body.replace('\n', '\\n')
    body = body.replace('\r', '\\r')
    body = body.replace('\t', '\\t')
    return body


for i in issues:
    i['labels'] = format_labels(i['labels']['nodes'])
    i['assignees'] = format_assignees(i['assignees']['nodes'])
    i['comments'] = i['comments']['totalCount']
    i['author'] = i['author']['login']
    i['body'] = format_body(i['body'])
    output.writerow(i)
