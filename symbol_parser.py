import csv

out_f=open("nasdaq_stocks.txt","w")
with open("nasdaq_stocks.csv","r") as csv_file:
    in_f = csv.reader(csv_file)
    for line in in_f:
        symbol=line[0]
        out_f.write(symbol+"\n")
out_f.close()