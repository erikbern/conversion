import os, zipfile

# You can download the data here: http://www.freddiemac.com/news/finance/sf_loanlevel_dataset.html
# Note that you need to register to download
# Put all the zip files in the 'freddie' folder before running this

d = 'freddie'
created = {}
defaulted = {}
terminated = {}

for fn in os.listdir(d):
    fn = os.path.join(d, fn)
    with zipfile.ZipFile(fn) as myzip:
        svcg_fn, = (zip_fn for zip_fn in myzip.namelist() if zip_fn.startswith('sample_svcg'))
        print(svcg_fn)
        for line in myzip.open(svcg_fn):
            data = line.decode('ascii').split('|')
            loan_id, month, balance_code, balance_date = data[0], data[1], data[8], data[9]
            created[loan_id] = min(created.get(loan_id, '999999'), month)
            if balance_code:
                terminated[loan_id] = balance_date
                if balance_code in ['03', '06', '09']:
                    defaulted[loan_id] = balance_date

def date_fmt(x):
    if not x:
        return ''
    else:
        return '%s-%s-01' % (x[0:4], x[4:6])

with open('data_freddie.tsv', 'w') as f:
    for k, month in created.items():
        f.write('%s\t%s\t%s\n' % (date_fmt(month), date_fmt(defaulted.get(k, '')), date_fmt(terminated.get(k, ''))))


