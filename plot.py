import datetime

def parse(date):
    if date:
        return datetime.date(*(int(p) for p in date.split('-')))
    else:
        return None

data = []
for line in open('data.tsv'):
    line = line.strip().split('\t')
    data.append(tuple(parse(item) for item in line))
print(data)
