import kisa_utils as kutils

__scriptPath = kutils.storage.Path.getMyAbsolutePath()
__scriptRootPath = kutils.storage.Path.directoryName(__scriptPath)

# __locationsDBPath = kutils.storage.Path.join(__scriptRootPath, 'db','locations.ubos.sqlite3')
__locationsDBPath = kutils.storage.Path.join(__scriptRootPath, 'db','locations.EC_Jul2022.sqlite3')

def __getSubLocations(path:str) -> list[dict]:
    '''
    follow path to get the sublocations in that path
    
    @param `path`: path to the location

    NB: path structure is as follows
        /{depth}/targetId,
        where {depth} follows the below structure
            /regionId/districtId/countyId/subCountyId/ParishId/villageId
        i.e; 
            {depth}=0, root ie `/`; getting all regions in the county
            {depth}=1, ie `/1/regionId`; getting districts in region
            {depth}=2, ie `/2/districtId`; getting counties in district
            {depth}=5, ie `/5/parishId`; getting villages in parish
            
    eg: 
        `path` = '/' -> return all regions
        `path` = '/{regionId}' -> return all districts in region whose id is {regionId}
        `path` = '/?/?/?/?/{parishId}' -> return all villages in parish whose id is {parishId}
    '''

    depth, targetId = None, None
    if '/'==path:
        depth = 0
    else:
        depth,targetId = path.split('/')[1:]
        depth = int(depth)

    depthLookupData = {
        0: {'table':'regions',      'constraintColumn': None,           'idColumn':'regionId'},
        1: {'table':'districts',    'constraintColumn':'regionId',      'idColumn':'districtId'},
        2: {'table':'counties',     'constraintColumn':'districtId',    'idColumn':'countyId'},
        3: {'table':'subCounties',  'constraintColumn':'countyId',      'idColumn':'subCountyId'},
        4: {'table':'parishes',     'constraintColumn':'subCountyId',   'idColumn':'parishId'},
        5: {'table':'villages',     'constraintColumn':'parishId',      'idColumn':'villageId'},
    }

    if depth not in depthLookupData:
        raise ValueError(f'ERR [kisa-locations:uganda] unknown depth {depth}')

    with kutils.db.Api(path=__locationsDBPath) as handle:
        lookupData = depthLookupData[depth]
        table, constraintColumn, idColumn = lookupData['table'], lookupData['constraintColumn'], lookupData['idColumn']

        return handle.fetch(
            table,
            [f'{idColumn} as id', 'name'], 
            (f'{constraintColumn}=?' if constraintColumn else '1')+' order by name asc',
            [targetId] if constraintColumn else [],
            returnDicts=True
        )

def getRegions() -> list[dict]: 
    '''
    get list of regions in the country.

    returns [{'id':str, 'name':str},...]
    '''
    return __getSubLocations('/')

def getDistricts(regionId:str) -> list[dict]: 
    '''
    get list of districts in a region.

    returns [{'id':str, 'name':str},...]
    '''
    return __getSubLocations(f'/1/{regionId}')

def getCounties(districtId:str) -> list[dict]: 
    '''
    get list of counties in a district.

    returns [{'id':str, 'name':str},...]
    '''
    return __getSubLocations(f'/2/{districtId}')

def getSubCounties(countyId:str) -> list[dict]: 
    '''
    get list of subCounties in a county.

    returns [{'id':str, 'name':str},...]
    '''
    return __getSubLocations(f'/3/{countyId}')

def getParishes(subCountyId:str) -> list[dict]: 
    '''
    get list of parishes in a subCounty.

    returns [{'id':str, 'name':str},...]
    '''
    return __getSubLocations(f'/4/{subCountyId}')

def getVillages(parishId:str) -> list[dict]: 
    '''
    get list of villages in a parish.

    returns [{'id':str, 'name':str},...]
    '''
    return __getSubLocations(f'/5/{parishId}')
