import csv, json, requests

from requests.exceptions import JSONDecodeError

INPUT_URLS = 'urls.txt'
OUTPUT_PROJECTS = 'data/projects.csv'
OUTPUT_EVENTS = 'data/events.csv'
MAX_PROJECTS = 10 #0000

def main():
    with open(INPUT_URLS, 'r') as f:
        urls = f.read().split('\n')
        print("Getting ready to harvest %d sites" % len(urls))
        
    eventcols, projectcols = get_datapackage_schema()
    print("Data Package loaded, Table Schema ready!")
    
    events = []
    projects = []
        
    for u in urls:
        if not u.strip(): continue
        print("--- Harvesting: %s" % u)
        ee, pp = get_events_projects(u)
        if ee is not None and pp is not None:
            events.extend(ee)
            projects.extend(pp)
    
    save_data(eventcols, events, projectcols, projects)
    print("Done.")
            

def get_datapackage_schema():
    """ Loads a Data Package containing the target Table Schema """
    projcols = eventcols = None
    with open('datapackage.json') as f:
        for res in json.load(f)['resources']:
            if 'events' in res['name']:
                eventcols = [ f['name'] for f in res['schema']['fields'] ]
            if 'projects' in res['name']:
                projcols = [ f['name'] for f in res['schema']['fields'] ]
    return eventcols, projcols
        

def get_events_projects(url):
    """ Fetches all the events and projects from a Dribdat URL """
    
    events_data = requests.get(url + '/api/events.json', timeout=5).json()
    all_events = events_data['events']
    for event in all_events:
        event['origin'] = url
    print('Collecting data from %d events' % len(all_events))

    count_total = 0
    project_data = {}
    for event in all_events:
        url_api = url + "/api/event/%d/projects.json" % event['id']
        print('.. event %d (%s)' % (event['id'], event['name']))
        try:
            proj_data = requests.get(url_api).json()
        except JSONDecodeError:
            print("!! invalid JSON data, skipping this server")
            return None, None
        if 'projects' in proj_data:
            project_data[event['id']] = proj_data['projects']
            count_total = count_total + len(proj_data['projects'])
        else:
            project_data[event['id']] = []
            print('!! no data for event %d' % event['id'])
        if count_total > MAX_PROJECTS: break

    all_projects = []
    for pd in project_data:
        for proj in project_data[pd]:
            proj['origin'] = url
            all_projects.append(proj)
    print('Downloaded a total of %d projects' % len(all_projects))
    
    return all_events, all_projects


def save_data(eventcols, events, projectcols, projects):
    """ Saves the events and projects to a file """
    
    with open(OUTPUT_EVENTS, "w") as f:
        cw = csv.DictWriter(f, eventcols, delimiter=',')
        cw.writeheader()
        cw.writerows(events)
    print("Wrote %s" % OUTPUT_EVENTS)
    with open(OUTPUT_PROJECTS, "w") as f:
        cw = csv.DictWriter(f, projectcols, delimiter=',')
        cw.writeheader()
        cw.writerows(projects)
    print("Wrote %s" % OUTPUT_PROJECTS)

if __name__ == "__main__":
    main()

