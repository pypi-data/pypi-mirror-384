from imsi.config_manager.schema.post_processing import PostProcessing


def test_minimal_config():
    """Test minimal configuration of Compiler."""

    arbitrary_config = {
        'name': 'post_processing',
        'compiler': {
            'name': 'post_processing',
            'asd_executable': 'post_processing',
            'banana_flags': ['flag1', 'flag2'],
            'arghhhh_matey!': ['option1', 'option2'],
        },
    }

    # test that any config works here!
    PostProcessing(**arbitrary_config)
