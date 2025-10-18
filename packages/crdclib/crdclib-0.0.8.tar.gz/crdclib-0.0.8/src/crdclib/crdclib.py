# A collection of random routines I use frequently
import yaml
import requests
import json
import re
import os
from bento_meta.model import Node, Property, Term, Tag, Edge

def readYAML(yamlfile):
    """This method reads a YAML file and returns a JSON object AND NOTHING ELSE

    :param yamlfile: A full path to the yaml file to be parsed
    :type yamlfile: String
    :return: A JSON object/dictionary representing the YAML file content
    :rtype: dictionary
    """

    with open(yamlfile) as f:
        yamljson = yaml.load(f, Loader=yaml.FullLoader)
    return yamljson


def writeYAML(filename, jsonobj):
    """Takes a filename and JSON object/dictionary and writes out a basic yaml file

    :param filename: A full path to the output file
    :type filename: String
    :param jsonobj: A dictionary to be written as YAML
    :type jsonobj: Dictionary
    """

    with open(filename, 'w') as f:
        yaml.dump(jsonobj, f)
    f.close()


def getCDERecord(cde_id, cde_version=None, verbose=False):
    """Queries the caDSR API with a CDE identifier and optional version, returns the full JSON object.  If no version is given, returns whatever the latest version is.

    :param cde_id: CDE Public identifier
    :type cde_id: Integer
    :param cde_version: The version of the CDE to be queried.  If not supplied the latest version will be returned
    :type cde_version: String, optional
    :return: If status_code == 200, a JSON object that is the full CDE record
    :rtype: dictionary
    :return: If status_code != 200, a string with error code and message
    :rtype: string
    :return: If HTTP error, the requests.HTTPError object
    :rtype: request.HTTPError
    """

    if verbose:
        print(f"CDE ID:\t{cde_id}\tVersion:\t{cde_version}")
    if cde_version is None:
        url = "https://cadsrapi.cancer.gov/rad/NCIAPI/1.0/api/DataElement/"+str(cde_id)
    else:
        url = "https://cadsrapi.cancer.gov/rad/NCIAPI/1.0/api/DataElement/"+str(cde_id)+"?version="+str(cde_version)
    headers = {'accept': 'application/json'}
    try:
        results = requests.get(url, headers=headers)
    except requests.exceptions.HTTPError as e:
        return (f"HTTPError:\n{e}")
    if results.status_code == 200:
        results = json.loads(results.content.decode())
        return results
    else:
        return (f"Error Code: {results.status_code}\n{results.content}")


def runBentoAPIQuery(url, query, variables=None):
    """Runs a GrpahQL Query against the Bento instance specified in the URL
    
    :param url: URL of the Bento instance API
    :type url: URL
    :param query: A valid GraphQL query
    :type query: String
    :param variables: a JSON object containing any variables for the provided query
    :type variables: dictionary, optional
    :return: If status_code == 200, a JSON object that is the full query response
    :rtype: dictionary
    :return: If status_code != 200, a string with error code and message
    :rtype: string
    :return: If HTTP error, the requests.HTTPError object
    :rtype: request.HTTPError
    """
    
    headers = {'accept': 'application/json'}
    try:
        if variables is None:
            results = requests.post(url, headers=headers, json={'query': query})
        else:
            results = requests.post(url, headers=headers, json={'query': query, 'variables': variables})
    except requests.exceptions.HTTPError as e:
        return (f"HTTPError:\n{e}")
        
    if results.status_code == 200:
        results = json.loads(results.content.decode())
        return results
    else:
        return (f"Error Code: {results.status_code}\n{results.content}")



def fullRunBentoAPIQuery(url, query, variables):
    """Runs a GrpahQL Query against the Bento instance specified in the URL and
    will keep querying until there are no more results.
    
     Note: The query and the variables MUST includ "first" and "offset"
    
    :param url: URL of the Bento instance API
    :type url: URL
    :param query: A valid GraphQL query
    :type query: String
    :param variables: a JSON object containing any variables for the provided query
    :type variables: dictionary, optional
    :return: If status_code == 200, a pandas dataframe
    :rtype: dataframe
    :return: If status_code != 200, a string with error code and message
    :rtype: string
    :return: If HTTP error, the requests.HTTPError object
    :rtype: request.HTTPError
    """

    # Safety check
    if 'first' not in variables:
        return None
    elif 'offset' not in variables:
        return None
    else:
        headers = {'accept': 'application/json'}
    
    #ISSUES:
    # How to determine if there are more entries
    # Need to increment offset varialbe
    # How to determine column headers
    # And/or how to load dataframe


def dhApiQuery(url, apitoken, query, variables=None):
    """Runs queries against the Data Hub Submission Portal API

    :param url: URL of the Submission Portal API
    :type url: URL
    :param apitoken: API Access token obtained from the Submission Portal
    :type apitoken: String
    :param query: A valid GraphQL query
    :type query: String
    :param variables: a JSON object containing any variables for the provided query
    :type variables: dictionary, optional
    :return: If status_code == 200, a JSON object that is the full query response
    :rtype: dictionary
    :return: If status_code != 200, a string with error code and message
    :rtype: string
    :return: If HTTP error, the requests.HTTPError object
    :rtype: request.HTTPError
    """

    headers = {"Authorization": f"Bearer {apitoken}"}
    try:
        if variables is None:
            result = requests.post(url=url, headers=headers, json={"query": query})
        else:
            result = requests.post(url=url, headers=headers, json={"query": query, "variables": variables})
        if result.status_code == 200:
            return result.json()
        else:
            return (f"Status Code: {result.status_code}\n{result.content}")
    except requests.exceptions.HTTPError as e:
        return (f"HTTPError: {e}")


def dhAPICreds(tier):
    """A simple way to retrieve the Data Hub submission URLs and API tokens

    :param tier: A string for the tier to return.  Must be one of prod, stage, qa, qa2, dev, dev2
    :type tier: String
    :return url: The URL for the requested tier
    :rtype: URL
    :return token: The API access token for the tier.
    :rtype: dictionary
    """

    url = None
    token = None
    if tier == 'prod':
        url = 'https://hub.datacommons.cancer.gov/api/graphql'
        token = os.getenv('PRODAPI')
    elif tier == 'stage':
        url = 'https://hub-stage.datacommons.cancer.gov/api/graphql'
        token = os.getenv('STAGEAPI')
    elif tier == 'qa':
        url = 'https://hub-qa.datacommons.cancer.gov/api/graphql'
        token = os.getenv('QAAPI')
    elif tier == 'qa2':
        url = 'https://hub-qa2.datacommons.cancer.gov/api/graphql'
        token = os.getenv('QA2API')
    elif tier == 'dev':
        url = 'https://hub-dev.datacommons.cancer.gov/api/graphql'
        token = os.getenv('DEVAPI')
    elif tier == 'dev2':
        url = 'https://hub-dev2.datacommons.cancer.gov/api/graphql'
        token = os.getenv('DEV2API')
    elif tier == 'localtest':
        url = 'https://this.is.a.test/url/graphql'
        token = os.getenv('LOCALTESTAPI')
    return {'url': url, 'token': token}



def getSTSCCPVs(id = None, version = None, model = False):
    """Uses the STS server to get permissible values and concept codes stored in MDB.  Easier than parsing the caDSR stuff. NOTE:  STS is only available on the NIH network
    
    :param id:  The CDE ID or the name/handle of the model.  Examples 'CDS', 'CTDC', 'ICDC'
    :type id: String
    :param version: The version number of the CDE or model
    :type modelversion: String
    :param model: Set to True to query for all PVs in a model.  False (default) for all PVs in a CDE
    :type model: Boolean
    :rtype: Dictionary of {concept code:permissible value}
    """

    base_url = "https://sts.cancer.gov/v1/terms/"
    headers = {'accept': 'application/json'}
    url = None
    
    if model:
        query = f"model-pvs/{id}/{version}/pvs"
    else: 
        if version is None:
            version = "1.00"
        query = f"cde-pvs/{id}/{version}/pvs"
        
    url = base_url+query
    headers = {'accept': 'application/json'}
    final = {}
    try:
        result = requests.get(url = url, headers = headers)

        if result.status_code == 200:
            # Need to do the parsing here
            cdejson = result.json()
            if type(cdejson['CDECode']) is list:
                if len(cdejson['permissibleValues'][0]) > 0:
                    for pv in cdejson['permissibleValues'][0]:
                        final[pv['ncit_concept_code']] = pv['value']
                else:
                    final = None
            elif len(cdejson['permissibleValues']) > 0:
                for pv in cdejson['permissibleValues']:
                    final[pv['ncit_concept_code']] = pv['value']
                else:
                    final = None
            else:
                final = None
            return final
        else:
            return (f"Error: {result.status_code}\n{result.content}")
    except requests.exceptions.HTTPError as e:
        return ("HTTP Error: {e}")



def getSTSPVList(cdeid, cdeversion):
    """Uses STS to get a list of permissible values for a CDE ID and version.  NOTE:  STS is only available on the NIH network

    :param id:  The CDE public ID
    :type id: String
    :param version: The version number of the CDE
    :type modelversion: String
    :rtype: List of [permissible value]
    """

    base_url = "https://sts.cancer.gov/v1/terms/"
    headers = {'accept': 'application/json'}
    url =  base_url+f"cde-pvs/{cdeid}/{cdeversion}/pvs"

    try:
        result = requests.get(url = url, headers = headers)
        
        if result.status_code == 200:
            pvlist = []
            cdejson = result.json()
            # If there is a list of CDE codes in the returned data, the PVs are also in a list
            if type(cdejson['CDECode']) is list:
                for entry in cdejson['permissibleValues']:
                    for pventry in entry:
                        if len(pventry) > 0:
                         pvlist.append(pventry['value'])
            else:
                # This is the normal approach.  If no PVs, an empty list is returned
                if len(cdejson['permissibleValues']) > 0:
                    for pv in cdejson['permissibleValues']:
                        pvlist.append(pv['value'])

        return pvlist
    except requests.exceptions.HTTPError as e:
        return ("HTTP Error: {e}")


def cleanString(inputstring, leavewhitespace=False):
    """Removes non-printing characters and whitespaces from strings
    
        :param string inputstring: The string to be processed
        :type intputstring: String
        :param leavewhitespace: Boolean, if True, uses regex [\\n\\r\\t?]+.  If False, uses regex [\\W]+
        :type leavewhitespace: Boolean, optional, default False
        :return: Processed string
        :rtype: String
    """

    if leavewhitespace:
        outputstring = re.sub(r"[\n\r\t?]+", '', inputstring)
        outputstring.rstrip()
    else:
        outputstring = re.sub(r"[\W]+", '', inputstring)
    return outputstring



def mdfAddNodes(mdfmodel, nodelist):
    """Adds node objects to an MDF model object

    :param mdfmodel: An MDF model object to which nodes will be added
    :type mdfmodel: MDF model object
    :param nodelist: A list of node names to be added to the MDF model
    :type nodelist: List of String
    :return: MDF Model with additional nodes added
    :rtype: MDF Model object
    """

    for nodename in nodelist:
        mdfmodel.add_node(Node({'handle': nodename}))
    return mdfmodel


def mdfAddProperty(mdfmodel, node_prop_dict, add_node = False):
    """Adss property objects to an MDF model object.  If requested, missing nodes will be added

    :param mdfmodel: An MDF model object to which nodes will be added
    :type mdfmodel: MDF model object
    :param node_prop_dict: A dictionary with an individual node name as key and a list of dictionaries containing property information {nodename:[{propery_description}]}
    :type node_prop_dict: Dictionary
    :param property_description: A dicionary {prop:property_name, isreq: Yes or No indictating if property is required, 'val': The property data type or 'value_set' if Enums are to be added, 'desc': Property description}
    :type property_description: Dictionary
    :param add_node: If set to true, any nodes found in node_prop_dict that are not already in the model will be added.
    :type add_node:  Boolean, default is False
    :return: MDF Model with additional properties added
    :rtype: MDF Model object
    """

    for node, properties in node_prop_dict.items():
        if add_node:
            if node not in list(mdfmodel.nodes):
                mdfmodel = mdfAddNodes(mdfmodel, [node])
        for prop_info in properties:
            propobj = Property({'handle': prop_info['prop'],
                                "_parent_handle": node,
                                'is_required': prop_info['isreq'],
                                'value_domain': prop_info['val'],
                                'desc': prop_info['desc']})
            nodeobj = mdfmodel.nodes[node]
            mdfmodel.add_prop(nodeobj, propobj)
        return mdfmodel

        
def mdfAddEnums(mdfmodel, nodename, propname, enumlist):
    """Adds an ENUM section to an existing property.

    :param mdfmodel: An MDF model object to which nodes will be added
    :type mdfmodel: MDF model object
    :param nodename: The name of the node the property belongs to
    :type nodename: String
    :param propname: The name of the property to add Enums
    :type propename: String
    :param enumlist: The list of enumerated values to be added to the ENUM section
    :type enumlist: List of string
    :return: MDF Model with ENUMS added.  Returns original model if node or property doesn't exist.
    :rtype: MDF Model object
    """

    # Check that the node and property exist
    if nodename in list(mdfmodel.model.nodes):
        if (nodename, propname) in list(mdfmodel.model.props):
            propobj = mdfmodel.model.props[nodename, propname]
            propobj.value_domain = 'value_set'
            mdfmodel.add_terms(propobj, *enumlist)
    return mdfmodel



def mdfAddTerms(mdfmodel, nodename, propname, termdict):
    """Adds a CDE Term section to an existing property.

    :param mdfmodel: An MDF model object to which terms will be added
    :type mdfmodel: MDF model object
    :param propname: The name of the property to add Enums
    :type propename: String
    :param termdict: A dictionary containing the information for the CDE. {'handle': property name, 'value':cde name, 'origin_version': cde version, 'origin_name': Source of the CDE, 'origin_id':cde idenfier, 'origin_definition': CDE Definition}
    :type termdict: Dictionary
    :return: MDF Model with Term added.  Returns original model if the property doesn't exist.
    :rtype: MDF Model object
    """
    
    if (nodename, propname) in list(mdfmodel.model.props):
        termobj = Term(termdict)
        propobj = mdfmodel.model.props[(nodename, propname)]
        mdfmodel.model.add_terms(propobj, termobj)
    return mdfmodel

def mdfAddEdges(mdfmodel, edgelist):
    """Adds edges between existing nodes.  Returns the MDF model object
    
    :param mdfmodel: An MDF model object to which terms will be added
    :type mdfmodel: MDF model object
    :param edgelist: A list of dictionary [{'handle': A name forthe edge, 'multiplicity': one-to-one, many-to-one, ect, 'src': the name of the source node], 'dst': the name of the destination node}]
    :type edgelist: List
    :return: MDF Model with Edges added.  Returns original model if the nodes doesn't exist.
    :rtype: MDF Model object
    """

    for edge in edgelist:
        if edge['src'] in list(mdfmodel.model.nodes):
            if edge['dst'] in list(mdfmodel.model.nodes):
                srcnode = mdfmodel.model.nodes[edge['src']]
                dstnode = mdfmodel.model.nodes[edge['dst']]
                edgeobj = Edge({'handle':edge['handle'], 'multiplicity':edge['multiplicity'], 'src':srcnode, 'dst':dstnode})
                mdfmodel.add_edge(edgeobj)
    return mdfmodel


def mdfAddTags(mdfmodel, objecttype, objectkey, tagdict):
    """Adds a tag to a node, property, or edge.

    :param mdfmodel: An MDF model object to which tags will be added
    :type mdfmodel: MDF model object
    :param objecttype: The entity to be tagged.  Must be one of 'node', 'property', 'edge'
    :type objecttype: String
    :param objectkey: The key used to find objects in MDF.  For nodes, it would be node name.  For properties it would by (nodename, propname).
    :type objectkey: String or tuple
    :param tagdict: A dictionary wtih the format {'key': key string, 'value': the value for the key}
    :type tagdict: Dictionary
    :return: MDF Model with tags added.  Returns original model if the nodes doesn't exist.
    :rtype: MDF Model object
    """

    tagtarget = None
    if objecttype == 'node':
        if objectkey in list(mdfmodel.model.nodes):
            tagtarget = mdfmodel.model.nodes[objectkey]
    elif objecttype == 'property':
        if objectkey in list(mdfmodel.model.props):
            tagtarget = mdfmodel.model.props[objectkey]
    elif objecttype == 'edge':
        if objectkey in list(mdfmodel.model.edges):
            tagtarget = mdfmodel.model.edges[objectkey]
    tagobj = Tag(tagdict)
    tagtarget.tags[tagobj.key] = tagobj
    return mdfmodel




    
