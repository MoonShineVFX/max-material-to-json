'''
Created on 2020-6-9

@todo: add ArrayParamater class output support
@author: noflame.lin
'''
import sys
pyd_path = r'C:\Users\linju\.p2\pool\plugins\org.python.pydev.core_7.2.0.201903251948\pysrc'
if pyd_path not in sys.path:
    sys.path.append(pyd_path)
import pydevd

import json
import pymxs

rt = pymxs.runtime


def recal_normal(obj):
    rt.addModifier(obj, rt.Edit_Normals())
    rt.collapseStack(obj)


def get_class_obj(cls_list, selected=True,):
    cls_objs = list()
    if selected:
        objs = [obj for obj in rt.selection]
    else:
        objs = [obj for obj in rt.Objects]
    for obj in objs:
        _, obj_cls = get_max_class(obj)
        if obj_cls in cls_list:
            cls_objs.append(obj)
    return cls_objs


def export_mat(filename):
    re = dict()
    objs = get_class_obj(('VRayProxy', 'Editable_Poly', 'Editable_mesh', 'PolyMeshObject'), selected=True)
    mats = list()
    for obj in objs:
        if not obj.material:
            continue
        if obj.material not in mats:
            mats.append(obj.material)

    for mat in mats:
        re.update(Conv.material_2_dic(mat))

    with open(filename, 'w') as f:
        f.write(json.dumps(re))

        return True


def export_table(filename):
    re = dict()
    objs = get_class_obj(('VRayProxy', 'Editable_Poly', 'Editable_mesh', 'PolyMeshObject'), selected=True,)
    for obj in objs:
        _full_name = obj_full_name(obj)
        val = re.get(_full_name, None)
        if val == None:
            if obj.mat is None:
                re[_full_name] = None
            else:
                re[_full_name] = obj.mat.name
        else:
            print('WRANGING!!! obj: %s has the same name!' % (obj.name))

    with open(filename, 'w') as f:
        f.write(json.dumps(re))

    return True


def export_abc(filename):
    
    def pre_process(obj, obj_class):
        if obj_class == 'VRayProxy':
            if obj.display != 4:
                print("set %s dispaly to 4" % (obj.name))
                obj.display = 4
        
        if obj_class == 'Editable_mesh':
            print("convrt %s to edit poly" % (obj.name))
            rt.convertTo(obj, rt.Editable_Poly)
            recal_normal(obj)

        if obj_class in ('Editable_Poly'):
            print("re_caculate %s's normal." % (obj.name))
            rt.addModifier(obj, rt.Edit_Normals())
            rt.collapseStack(obj)
        
        # rename if there are weird char in name
        if "/" in obj.name:
            old_name = obj.name
            obj.name = obj.name.replace('/','-')
            print('rename obj from %s to %s' %(old_name, obj.name))
            
    if rt.AlembicExport.CoordinateSystem != "Maya":
        rt.AlembicExport.CoordinateSystem = rt.Name("Maya")
    if rt.AlembicExport.ArchiveType != "Ogawa":
        rt.AlembicExport.ArchiveType = rt.Name("Ogawa")
    if rt.AlembicExport.ParticleAsMesh:
        rt.AlembicExport.ParticleAsMesh = False
    if rt.AlembicExport.CacheTimeRange != "Currentframe":
        rt.AlembicExport.CacheTimeRange = rt.Name("Currentframe")
    if rt.AlembicExport.ShapeName:
        rt.AlembicExport.ShapeName = False
    
    org_selected = [obj for obj in rt.selection]
    objs = get_class_obj(('VRayProxy', 'Editable_Poly', 'Editable_mesh', 'PolyMeshObject'), selected=True)
    for obj in objs:
        _, obj_cls = get_max_class(obj)
        pre_process(obj, obj_cls)
    rt.select(objs)
    abc_cls = getattr(rt, "Alembic_Export", None)
    if abc_cls is None:
        raise RuntimeError('No ABC Expot Plugin')
    rt.exportFile(filename, rt.Name('noPrompt'), selectedOnly=True, using=abc_cls)
    rt.select(org_selected)
    return True


def trail_to_number(text, run=1):
    '''convert trail word to digital number'''
    
    try:
        int(text[-1:])
    except ValueError:
        return text, 0

    try:
        index_str = text[-(run + 1):]
        index_num = int(index_str)
        if index_num < 0:
            raise ValueError()
        if run == len(text):
            return None , index_num
        run += 1
#         print("%s, %s to next" %(index_str, index_num))
        return trail_to_number(text, run=run)
    except ValueError:
        index_str = text[-run:]
        pre_name = text[:-run]
        return pre_name, int(index_str)


def UniqueMatName():
    
    names = dict()
    
    def wrapper(name):
        times = names.get(name, 0)
        if times == 0:
            names[name] = 1
            return name
        else:
            pre_name, surfix = trail_to_number(name)
            if pre_name:
                new_name = pre_name + '{:03d}'.format(surfix + 1)
            else:
                new_name = '{:03d}'.format(surfix + 1)
            return wrapper(new_name)

    return wrapper


unique_name = UniqueMatName()


def collect_scenes_material():
    
    def do_mat(mat, re):
        if mat not in re: re.append(mat)
        _, mat_cls = get_max_class(mat)
        attr_map = MappingTool.build_material(mat_cls)
        props = attr_map[mat_cls]
        for p_name, p_type in props.items():
            if p_type == ('material'):
                value = getattr(mat, p_name, None)
                if value:
                    do_mat(value, re)
            elif p_type == 'material array':
                value = getattr(mat, p_name, None)
                if value :
                    [do_mat(mat) for mat in value if mat is not None]

    re = list()
    for mat in rt.sceneMaterials:
        do_mat(mat, re)
    return re


def make_matname_unique():
    mats = collect_scenes_material()
    for mat in mats:
        mat.name = unique_name(mat.name)


def obj_full_name(obj):
    
    def parent_(obj, child_name):
        full_name = obj.name + u'/' + child_name
        if obj.parent is None:
            return u'/' + full_name
        else:
            return parent_(obj.parent, full_name)
        
    full_name = obj.name
    if obj.parent is not None:
        full_name = parent_(obj.parent, full_name)
    else:
        full_name = u'/' + obj.name
    return full_name


def get_max_class(max_obj):
    cls_of_max_obj = rt.classOf(max_obj)
    des = repr(cls_of_max_obj)
    _, sup_cls_name, cls_name = des.split('<')
    cls_name = cls_name.split('>')[0]
    if cls_name == 'UndefinedClass':
        raise RuntimeError(u'UndefinedClass: %s' % (max_obj.name))
    return sup_cls_name, cls_name


class MappingTool(object):
    cls_ = {'material':None, 'texturemap':None, 'shader':None}
    value_type = set()
    _unsupport_material = ['MorpherMaterial']
    _unsupport_texture = []
    _unsupport_value = []

    @classmethod
    def _build_cls_list(cls, cls_name):
        re = dict()
        cls_list = rt.stringStream("")
        rt.showClass("*:{}".format(cls_name), to=cls_list)
        cls_list = str(cls_list)
        cls_list_sp = cls_list.split('\n')
        cls_list_sp.pop()
        cls_li = cls_list_sp.pop(0)
        re[cls_li.split(' ')[0].split(':')[1][1:]] = None
        for cls_li in cls_list_sp:
            re[cls_li.split(' ')[0]] = None
        return re
    
    @classmethod
    def _build_prop_list(cls, max_class):
        re = dict()

        prop_list = rt.stringStream("")
        rt.showClass("{}.*".format(max_class), to=prop_list)
        prop_list = str(prop_list)
        prop_list_sp = prop_list.split('\n')
        prop_list_sp.pop()
        prop_list_sp.pop(0)

        for prop_li in prop_list_sp:
            prop_name, prop_type = prop_li.split(':')
            prop_name = prop_name.strip()
            prop_name = prop_name.split(' ')[0]
            prop_name = prop_name[1:]
            prop_type = prop_type.strip()
            re[prop_name] = prop_type
            cls.value_type.add(prop_type)
        return re

        @classmethod
        def build_material(cls, material_class):
            return cls.build_complex('material', material_class)

        @classmethod
        def build_texmap(cls, texmap_class):
            return cls.build_complex('texturemap', texmap_class)
        
        @classmethod
        def build_shader(cls, shader_class):
            return cls.build_complex('shader', shader_class)

#     @classmethod
#     def build_material(cls, material_class):
#         if cls.cls_['material'] is None:
#             cls.cls_['material'] = cls._build_cls_list('material')
#         if cls.cls_['material'].get(material_class, None) is None:
#             cls.cls_['material'][material_class] = cls._build_prop_list(material_class)
#     
#         return cls.cls_['material'][material_class]
# 
#     @classmethod
#     def build_texmap(cls, texmap_class):
#         if cls.cls_['texturemap'] is None:
#             cls.cls_['texturemap'] = cls._build_cls_list('texturemap')
#         if cls.cls_['texturemap'].get(texmap_class, None) is None:
#             cls.cls_['texturemap'][texmap_class] = cls._build_prop_list(texmap_class)
#         
#         return cls.cls_['texturemap'][texmap_class]
    
    @classmethod
    def build_complex(cls, sup_cls, the_cls):
        if cls.cls_[sup_cls] is None:
            cls.cls_[sup_cls] = cls._build_cls_list(sup_cls)
        if cls.cls_[sup_cls].get(the_cls, None) is None:
            cls.cls_[sup_cls][the_cls] = cls._build_prop_list(the_cls)
        
        return cls.cls_[sup_cls][the_cls]
    

class Conv(object):
    
    @classmethod
    def _complex_maxobject(cls, maxobj):
        re = dict()
        sup_cls, obj_cls = get_max_class(maxobj)
        if sup_cls == 'material':
            props = MappingTool.build_material(obj_cls)
        elif sup_cls == 'textureMap':
            props = MappingTool.build_texmap(obj_cls)
        else:
            raise RuntimeError("%s should not in complex func" % (obj_cls))
        
        return cls._collect_properties_value(maxobj, props)
    
#         re = dict()
#         for p_name, p_type in props.items():
#             value = getattr(maxobj, p_name, None)
#             if value is None:
#                 re[p_name] = None
#             else:
#                 func = cls.mapping(p_type)
#                 re[p_name] = func(value)
#         return re

    @classmethod
    def _complex_property(cls, obj, property_name):
#         sup_cls, obj_cls = get_max_class(obj)
        value_ = getattr(obj, property_name)
        if property_name in ("shaderByName"):
            props = MappingTool.build_shader(value_)
        else:
            raise RuntimeError("%s should not in complex func" % (value_))
        
        return cls._collect_properties_value(obj, props)
    
    @classmethod
    def _collect_properties_value(cls, obj, props):
        re = dict()
        for p_name, p_type in props.items():
            value = getattr(obj, p_name, None)
            if value is None:
                re[p_name] = None
            else:
                func = cls.mapping(p_type)
                re[p_name] = func(value)
        return re

    @classmethod
    def mapping(cls, max_class_name):
        max_class_name = max_class_name.lower()
        fn_name = max_class_name.replace(' ', '_') + '_2_dic'
        func = getattr(cls, fn_name, cls._not_support)
        if func == cls._not_support:
            pydevd.settrace("192.168.1.35", suspend=True)
        return func

    @classmethod
    def _not_support(cls, item):
        sup_, cls_ = get_max_class(item)
        return '%s:%s is not support for output' % (sup_, cls_)

    @classmethod
    def frgba_color_2_dic(cls, color_):
        return cls.rgb_color_2_dic(color_)

    @classmethod
    def filename_2_dic(cls, file_):
        return {'filename':file_}

    @classmethod
    def color_2_dic(cls, val):
        return cls.rgb_color_2_dic(val)

    @classmethod
    def rgb_color_2_dic(cls, color):
        return {u'color':
                {u'r':color.r,
                 u'g':color.b,
                 u'b':color.g,
                 u'a':color.a}}

    @classmethod
    def rgb_color_array_2_dic(cls, color_array):
        return {u'rgb_color_array':[cls.rgb_color_2_dic(color) for color in color_array]}

    @classmethod
    def boolean_2_dic(cls, bool_):
        return {u'boolean':bool_}

    @classmethod
    def boolean_array_2_dic(cls, boolean_array):
        return {u'boolean_array':[cls.boolean_2_dic(bool_) for bool_ in boolean_array]}

    @classmethod
    def percent_2_dic(cls, float_):
        return cls.float_2_dic(float_)

    @classmethod
    def float_2_dic(cls, float_):
        return {u'float':float_}

    @classmethod
    def double_2_dic(cls, dou):
        return {u'double':dou}

    @classmethod
    def integer_2_dic(cls, int_):
        return cls.int_2_dic(int_)

    @classmethod
    def int_2_dic(cls, int_):
        return {u'int':int_}

    @classmethod
    def int_array(cls, ints):
        return {u'int_array':[cls.int_2_dic(int_) for int_ in ints]}

    @classmethod
    def worldunits_2_dic(cls, wu):
        return cls.float_2_dic(wu)

    @classmethod
    def string_2_dic(cls, str_):
        return {u'string': str_}

    @classmethod
    def string_array_2_dic(cls, strs):
        return {u'string_array':[cls.string_2_dic(str_) for str_ in strs]}

    @classmethod
    def material_2_dic(cls, mat):
        sup_cls, mat_class = get_max_class(mat)
        re = {u'max_superclass':sup_cls, u'max_class':mat_class}
        re.update(cls._complex_maxobject(mat))
        if mat_class in ("Standardmaterial", "Standard"):
            shader_re = cls._complex_property(mat, 'shaderByName')
            re.update(shader_re)
        return {mat.name:re}

    @classmethod
    def material_array_2_dic(cls, mats):
        return {u'material_array':
                [cls.material_2_dic(mat) for mat in mats if mat]}
    
    @classmethod
    def texturemap_2_dic(cls, txmap):
        sup_cls, map_class = get_max_class(txmap)
        re = {u'max_superclass':sup_cls, u'max_class':map_class}
        re.update(cls._complex_maxobject(txmap))
        return {txmap.name:re}

    @classmethod
    def texturemap_array_2_dic(cls, txmaps):
        return {u'texturemap_array':
                [cls.texturemap_2_dic(txmap) for txmap in txmaps if txmap]}

    @classmethod
    def point3_2_dic(cls, p3):
        return {u'point3': {u'x':p3.x,
                            u'y':p3.y,
                            u'z':p3.z}}

    @classmethod
    def angle_2_dic(cls, ang):
        return {u'angle': ang}

    @classmethod
    def float_array_2_dic(cls, float_ary):
        return {u'float_array':
                [cls.float_2_dic(flo) for flo in float_ary]}

    @classmethod
    def int_array_2_dic(cls, ints_):
        return {u'int_array':
                [cls.integer_2_dic(int_) for int_ in ints_]}

    @classmethod
    def percent_array_2_dic(cls, percents):
        return {u'percent array':
                [cls.percent_2_dic(per for per in percents)]}
