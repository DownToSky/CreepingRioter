import crawler
import networkx as nx

key = ""
with open("key", 'r') as cred_file:
    lines = [line for line in cred_file]
    key = lines[0].strip()
cp = crawler.Crawler(key, "Doublelift", "NA")
cp.process(1)
l = cp.G.edges(data = True)
names = nx.get_node_attributes(cp.G, "name")
sl = dict()
for e in l:
    sl[(names[e[0]],names[e[1]])] = e[2]['weight']
sk = sorted(sl, key=lambda relation: sl[relation])
for k in sk:
    print("{}:{}".format(k,sl[k]))
cp.Draw()
