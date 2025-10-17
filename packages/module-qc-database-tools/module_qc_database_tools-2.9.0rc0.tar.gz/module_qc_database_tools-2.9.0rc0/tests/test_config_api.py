# documenting for how we want to test the API later
"""
if __name__ == '__main__':
    # Initialize the API and start with an empty configuration
    api = ChipConfigAPI()

    # This is a scratch test demo: wipe-out all in the beginning
    #api.db.fe_configs.delete_many( {} )
    #api.db.fe_config_revision.delete_many( {} )

    api.create_config( '20UPGXF0000013', 'MODULE/INITIAL_WARM' )

    config_id = api.checkout( '20UPGXF0000013', 'MODULE/INITIAL_WARM' )
    print(f'Initial configuration ID: {config_id}')
    api.info( config_id )

    # Make the first revision, adding some nested objects
    with open('input_cfg.json') as f:
        input_fecfg = json.load(f)
        api.commit( config_id, input_fecfg, "commit with input_cfg.json")

    output_fecfg = api.get_config( config_id, add_pixel_cfg = True )

    with open('output_cfg.json', 'w') as f:
        json.dump(output_fecfg, f)


    # Compare two configs with md5
    hashes = []
    for f in ['input_cfg.json', 'output_cfg.json']:
        with open( f, 'rb' ) as fp:
            data = fp.read()
            md5 = hashlib.md5(data).hexdigest()

    # Validation
    assert( all( x == hashes[0] for x in hashes ) )

    print('config I/O through mongodb was validated' )
"""
