# -*- coding: utf-8 -*-


def set_field_permissions(schema, mapping={}, exceptions=['portal_type', 'id']):
    """
    """

    for field in schema.fields():
        if field.getName() not in exceptions:
            default = ('liege.urban: External Reader', 'liege.urban: Internal Editor')
            read_permission, write_permission = mapping.get(field.schemata, default)
            if read_permission:
                field.read_permission = read_permission
            if write_permission:
                field.write_permission = write_permission

    return schema


def set_environment_field_permissions(schema, mapping={}, exceptions=['portal_type', 'id']):
    """
    """

    for field in schema.fields():
        if field.getName() not in exceptions:
            default = ('View', 'Modify portal content')
            read_permission, write_permission = mapping.get(field.schemata, default)
            if read_permission:
                field.read_permission = read_permission
            if write_permission:
                field.write_permission = write_permission

    return schema
