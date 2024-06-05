import matplotlib.pyplot as plt
# import matplotlib.patches

def get_new_plot(name):
    f = plt.figure(name)
    return (f, f.subplots())

def export_plot(path):
    plt.savefig(path)

def render_plot():   
    plt.show()
    
def generate_piechart(sites, category='visits', th=0):
    figure, axes = get_new_plot("HistoryLane Pie Chart")
    # 3/13/24:
    # This is inefficient, because it requires the Python runtime to copy the array whenever it expands past
    # its bounds. However, because items in sites are often skipped for being None or being too small (an
    # indeterminate number each time), it is not feasible to do fixed-length array allocation here to be lighter weight.
    # Because matplotlib only accepts Python arrays, it doesn't make sense to use a more sensible data structure (e.g.,
    # a linked list), because I would have to copy that into an array anyway, which is still computationally expensive.
    visits = []
    visit_labels = []
    counter = 0
    kuiper_belt = 0 
    for i in sites:
        if i is None: continue
        if len(sites[i]) < th:
            kuiper_belt += len(sites[i])
            continue
        
        visits.append(len(sites[i]))
        visit_labels.append(i)
        counter += 1
        
    if kuiper_belt > 0:
        visits.append(kuiper_belt)
        visit_labels.append('Everything Else')

    axes.pie(visits, labels=visit_labels)
    plt.tight_layout()

def generate_barchart(sites, label_by='title', th=0):
    figure, axes = get_new_plot("HistoryLane Bar Chart")
    axes.set_xticks(range(len(sites) + 1))
    axes.set_yscale('log')
    axes.tick_params(axis='x', labelrotation=90)
    ticklabels = [None] * (len(sites) + 1)
    counter = 0
    kuiper_belt = 0
    for i in sites:
        if i is None: continue
        if len(sites[i]) < th:
            kuiper_belt += len(sites[i])
            continue
        
        axes.bar(counter, len(sites[i]), label=i)
        ticklabels[counter] = i
        counter += 1

    if kuiper_belt > 0:
        axes.bar(counter, kuiper_belt, label='Everything Else')
        ticklabels[counter] = 'Everything Else'
        
    axes.set_xticklabels(ticklabels)
    plt.tight_layout()

def generate_scatterplot(sites, hcategory='counter', vcategory='duration', th=0):
    figure, axes = get_new_plot("HistoryLane Scatterplot")
    xaxis = []
    yaxis = []
    # Removed the aggregate category for things falling below the threshold of notice - it doesn't make sense given this
    # graph's purpose
    # 11/3/23 - this used to call axes.xscale(), which now raises an AttributeError
    # perhaps a version upgrade changed the API?
    axes.set_xscale('log')
    axes.set_yscale('log')

    for i in sites:
        if i is None: continue
        if len(sites[i]) < th:
            continue
        
        for j in sites[i]:
            xaxis.append(j[hcategory])
            yaxis.append(j[vcategory])

        axes.scatter(xaxis, yaxis)

        xaxis = []
        yaxis = []

    plt.tight_layout()
