from artinator import tool


def test_tool():
    class TestTool(tool.Tool):
        description = 'test tool description'

        bar = tool.Parameter('bardesc')
        foo = tool.Parameter('desc', type='int', required=False)

    assert TestTool().name == 'test_tool'

    assert TestTool()._parameters['bar'].description == 'bardesc'
    assert TestTool()._parameters['bar'].name == 'bar'
    assert TestTool()._parameters['bar'].type == 'string'
    assert TestTool()._parameters['bar'].required

    assert TestTool()._parameters['foo'].description == 'desc'
    assert TestTool()._parameters['foo'].name == 'foo'
    assert TestTool()._parameters['foo'].type == 'int'
    assert not TestTool()._parameters['foo'].required

    assert TestTool()._parameters['foo'].definition() == {
        'type': 'int',
        'description': 'desc',
    }

    assert TestTool().definition() == {
        'type': 'function',
        'function': {
            'name': 'test_tool',
            'description': 'test tool description',
            'parameters': {
                'type': 'object',
                'required': ['bar'],
                'properties': {
                    'bar': {
                        'type': 'string',
                        'description': 'bardesc',
                    },
                    'foo': {
                        'type': 'int',
                        'description': 'desc',
                    },
                },
            }
        }
    }
