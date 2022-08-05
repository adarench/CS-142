"""
.. versionadded:: R15.037

.. seealso:: All plugins examples starting with *py-sculpt* prefix in :maxongithub:`the GitHub repository <plugins/>`.
"""
from c4d import BaseTag
from c4d import BaseObject
from c4d import BaseList2D


def MakeSculptObject(obj, doc):
    """
    Adds a :class:`SculptTag` to the :class:`PolygonObject <c4d.PolygonObject>` *obj*.

    .. note::

        If one does not exist then return the :class:`SculptObject` that the newly created :class:`SculptTag` references.

    :type obj: c4d.PolygonObject
    :param obj: The :class:`PolygonObject <c4d.PolygonObject>` to add the :class:`SculptTag` to.
    :type doc: c4d.documents.BaseDocument
    :param doc: The document that *obj* belongs to.
    :rtype: :class:`SculptObject`
    :return: The :class:`SculptObject` that the :class:`SculptTag` is referencing.
    """


def GetSelectedSculptObject(doc):
    """
    Gets the currently selected :class:`SculptObject` in the document.

    .. note::

        This will be the first selected :class:`PolygonObject <c4d.PolygonObject>` that has a :class:`SculptTag`.

    :type doc: c4d.documents.BaseDocument
    :param doc: The document to search.
    :rtype: :class:`SculptObject`
    :return: The currently selected :class:`SculptObject`, or **None** if none is selected.
    """


class SculptTag(BaseTag):
    """
    | When a :class:`PolygonObject <c4d.PolygonObject>` is made sculptable it will contain a :class:`SculptTag <c4d.modules.sculpting.SculptTag>`.
    | Each :class:`SculptTag <c4d.modules.sculpting.SculptTag>` references a :class:`SculptObject <c4d.modules.sculpting.SculptObject>` in the Document.
    | This :class:`SculptObject <c4d.modules.sculpting.SculptObject>` contains all the layers and offsets used by the sculpt tools.

    .. versionadded:: R15.037

    .. warning::

        | The class :class:`SculptTag <c4d.modules.sculpting.SculptTag>` cannot be instantiated.
        | :func:`MakeSculptObject() <c4d.modules.sculpting.MakeSculptObject>` function should be used instead.
    """

    def GetSculptObject(self):
        """
        Get the :class:`SculptObject <c4d.modules.sculpting.SculptObject>` for this :class:`SculptTag <c4d.modules.sculpting.SculptTag>`.

        :rtype: c4d.modules.sculpting.SculptObject
        :return: The :class:`SculptObject <c4d.modules.sculpting.SculptObject>` that this tag references.
        """


class SculptObject(BaseObject):
    """
    | A :class:`SculptObject <c4d.modules.sculpting.SculptObject>` is what you use to interact with the data referenced by a :class:`SculptTag <c4d.modules.sculpting.SculptTag>` (:meth:`SculptTag.GetSculptObject`).
    | The :class:`SculptTag <c4d.modules.sculpting.SculptTag>` on a :class:`PolygonObject <c4d.PolygonObject>` references a :class:`SculptObject <c4d.modules.sculpting.SculptObject>` that is stored in a scene hook within the document.
    | When the :class:`SculptTag <c4d.modules.sculpting.SculptTag>` is deleted this :class:`SculptObject <c4d.modules.sculpting.SculptObject>` is also deleted.

    .. versionadded:: R15.037
    """
    def GetSubdivisionCount(self):
        """
        Get the number of subdivisions that this sculpt object currently has; i.e. how many times it has been subdivided by the user.

        :rtype: int
        :return: The number of subdivision levels.
        """

    def GetPolygonCopy(self, level, includeTopLevels):
        """
        Get a copy of the sculpt object at a specific subdivision level.

        :type level: int
        :param level: The subdivision level to copy the :class:`PolygonObject <c4d.PolygonObject>` at. 
        :type includeTopLevels: bool
        :param includeTopLevels: 
            | If True includes all the detail from any layers that are above subdivisionLevel.
            | If false includes only the sculpting data for all layers up to and including the subdivisionLevel specified. 
            
        :rtype: c4d.PolygonObject
        :return: The :class:`PolygonObject <c4d.PolygonObject>` for the subdivision *level*.
        """

    def GetOriginalObject(self):
        """
        Get the original :class:`PolygonObject <c4d.PolygonObject>` that the :class:`SculptTag <c4d.modules.sculpting.SculptTag>` is applied to.

        :rtype: c4d.PolygonObject
        :return: The original :class:`PolygonObject <c4d.PolygonObject>`.
        """

    def GetPolygonCount(self):
        """
        Get the number of polygons at the current subdivision level.

        :rtype: int
        :return: The number of polygons.
        """

    def GetPointCount(self):
        """
        Get the number of points at the current subdivision level.

        :rtype: int
        :return: The number of points.
        """

    def GetCurrentLevel(self):
        """
        Gets the current subdivision level that the sculpt object is currently at.

        :rtype: int
        :return: The current subdivision level.
        """

    def GetMemoryUsage(self):
        """
        Get the amount of memory currently used for this sculpt object. This does not include any memory used by the Viewport.

        :rtype: int
        :return: The memory used in bytes.
        """

    def GetCurrentLayer(self):
        """
        Get the currently layer, or folder, selected for this sculpt object.

        :rtype: c4d.modules.sculpting.SculptLayerBase
        :return: The current sculpt layer or folder.
        """

    def AddLayer(self):
        """
        Create a new layer on the sculpt object at the current subdivision level.

        :rtype: c4d.modules.sculpting.SculptLayer
        :return: The sculpt layer added.
        """

    def AddFolder(self):
        """
        Create a new folder for the sculpt object.

        :rtype: c4d.modules.sculpting.SculptFolder
        :return: The sculpt folder added.
        """

    def DeleteSelectedLayer(self):
        """
        Deletes the currently selected layer (or folder) on the sculpt object (as specified in the Sculpting Layer Manager UI).

        .. note::

            If the currently selected layer is a folder then it will only delete the folder if all the layers that are contained in that folder are at the same subdivision level as the current subdivion level.

        :rtype: bool
        :return: **True** if the layer was deleted, otherwise **False**.
        """

    def Update(self):
        """
        Recomposites all the layers and updates the sculpt object.
        """

    def GetVertexNormal(self, index):
        """
        Get the vertex normal for the polygon object at *index* and at the current subdivision level.

        :type index: int
        :param index: The index of the vertex.
        :raise IndexError: If the vertex *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :rtype: c4d.Vector
        :return: The vertex normal.
        """

    def GetFaceNormal(self, index):
        """
        Gets the face normal for the polygon object at *index* and at the current subdivision level.

        .. versionadded:: R17.032

        :type index: int
        :param index: The index of the face.
        :raise IndexError: If the face *index* is out of range : *0<=index<*:meth:`GetPolygonCount`.
        :rtype: c4d.Vector
        :return: The face normal.
        """

    def GetPoint(self, index):
        """
        Get read-only access to the point at *index* that will be used for the polygon object at the current subdivision level.

        :type index: int
        :param index: The index of the point.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :rtype: c4d.Vector
        :return: The point.
        """

    def Subdivide(self):
        """
        Subdivide the sculpt object to the next level.

        .. note::

            | This method will only work if the sculpt object is already at the top most level and the memory limit (as specified in the preferences) has not been exceeded and also only if there is enough memory on the user's computer to successfully do the subdivision.

        :rtype: bool
        :return: **True** if the object was successfully subdivided, otherwise **False**.
        """

    def IncreaseSubdivisionLevel(self):
        """
        | Increase the subdivision level to the next highest level.
        | If it is already at the top subdivision level then it will do nothing.

        :rtype: bool
        :return: **True** if it was able go up a level, otherwise **False**.
        """

    def DecreaseSubdivisionLevel(self):
        """
        | Decrease the subdivision level to the down one level.
        | If it is already at level 0 then it will do nothing.

        :rtype: bool
        :return: **True** if it was able go down a level, otherwise **False**.
        """

    def GetFirstLayer(self):
        """
        Get the first layer. This is usually the Base Object layer.

        :rtype: c4d.modules.sculpting.SculptLayerBase
        :return: The first layer.
        """

    def GetBaseLayer(self):
        """
        Get the Base Object layer, which is the special layer that has multiple :class:`SculptLayerData <c4d.modules.sculpting.SculptLayerData>` children, one for each subdivison level, that allows the user to sculpt on while at any subdivision level.

        :rtype: c4d.modules.sculpting.SculptLayerBase
        :return: The Base Object layer.
        """

    def IsFrozen(self):
        """
        | Check if the sculpt object is frozen.
        | This is also able to be set on the :class:`SculptTag <c4d.modules.sculpting.SculptTag>` in Cinema 4D's UI.

        :rtype: bool
        :return: **True** if the object is frozen, otherwise **False**.
        """

    def SetFrozen(self, frozen):
        """
        Sets the frozen state of the sculpt object. In Cinema 4D UI this is shown in the :class:`SculptTag <c4d.modules.sculpting.SculptTag>`. When the object is frozen no changes to the sculpt object or any of its layers are allowed.

        .. note::

            | If the polygon object has a `Phong` tag it will also become active when the sculpt object is frozen.
            | When not Frozen then the sculpt object uses its own internal vertex normals and disables the `Phong` tag on the polygonobject.

        :type frozen: bool
        :param frozen: The frozen state.
        """

    def GetAllowDeformations(self):
        """
        Check if the object allows to be deformed by any deformers. This is also able to be set on the :class:`SculptTag <c4d.modules.sculpting.SculptTag>` in Cinema 4D's UI.

        .. note::

            | This option only works if the object is also frozen.
            | When both these options are enabled, any deformers that are children of the polygon object that the sculpt tag is applied to, will be able to deform the object in the viewport.

        :rtype: bool
        :return: **True** if the sculpt object allows deformations, otherwise **False**.
        """

    def SetAllowDeformations(self, allowDef):
        """
        | Set the `Allow Deformations` checkbox thereby allowing any deformers to have an effect on the display of the sculpt object, as long as it is also frozen.
        | This option can also be found in the :class:`SculptTag <c4d.modules.sculpting.SculptTag>`'s UI.

        :type allowDef: bool
        :param allowDef: **True** to allow deformations, otherwise **False**.
        """

    def UpdateCollision(self):
        """
        Updates any collision data after any changes to the sculpt layer offsets have been made. This is required before you call the :meth:`HitScreen`/:meth:`HitObject` methods.
        """

    def NeedCollisionUpdate(self, fullUpdate):
        """
        Tells the sculpt object that it requires a collision update before the user tries to use any of the sculpt tools. Then next time a user tries to use a tool it will first call :meth:`UpdateCollision` to ensure that the :meth:`HitScreen`/:meth:`HitObject` calls will be correct.

        :type fullUpdate: bool
        :param fullUpdate: Set to **True** to update the full mesh. This is not always required.
        """

    def HitScreen(self, bd, mx, my, backfaces):
        """
        From a viewport cast a ray, in screen space, onto the sculpt object and return any data if the ray hits the object.

        .. note::

            This will return the closest hit point if multiple intersections are found.

        .. note::

            To use the `Hit` functions the mesh must be unfrozen and both :meth:`NeedCollisionUpdate(True) <SculptObject.NeedCollisionUpdate>` and :meth:`UpdateCollision` should be called to initialize the collision data.

        :type bd: c4d.BaseDraw
        :param bd: The :class:`BaseDraw <c4d.BaseDraw>` that the user is casting the ray from.
        :type mx: float
        :param mx: The X coordinate (i.e. mouse coordinate) in screen space.
        :type my: float
        :param my: The Y coordinate (i.e mouse coordinate) in screen space.
        :type backfaces: bool
        :param backfaces: Allow back facing polygons to be hit tested.
        :rtype: dict{**distance**: float, **normal**: :class:`Vector <c4d.Vector>`, **point**: :class:`Vector <c4d.Vector>`, **polygon**: int}
        :return: The intersection data will be returned if the object was hit:

            distance: The distance from the ray point.
            normal: The normal of the hitpoint on the surface of the object in its local coordinate system.
            point: Location of the hit point on the surface of the object in its local coordinate system.
            polygon: The polygon that was hit.
        """

    def HitObject(self, rayp, rayv, backfaces):
        """
        Given a ray in object space do a hit intersection against the sculpt object and return any data if the ray hits the object.

        .. note::

            This will return the closest hit point if multiple intersections are found.

        .. note::

            To use the `Hit` functions the mesh must be unfrozen and both :meth:`NeedCollisionUpdate(True) <SculptObject.NeedCollisionUpdate>` and :meth:`UpdateCollision` should be called to initialize the collision data.

        :type rayp: c4d.Vector
        :param rayp: The starting position of the ray in object space.
        :type rayv: c4d.Vector
        :param rayv: The direction the ray is pointing.
        :type backfaces: bool
        :param backfaces: Allow back facing polygons to be hit tested.
        :rtype: dict{**distance**: float, **normal**: :class:`Vector <c4d.Vector>`, **point**: :class:`Vector <c4d.Vector>`, **polygon**: int}
        :return: The intersection data will be returned if the object was hit:

            distance: The distance from the ray point.
            normal: The normal of the hitpoint on the surface of the object in its local coordinate system.
            point: Location of the hit point on the surface of the object in its local coordinate system.
            polygon: The polygon that was hit.
        """

    def StartUndo(self):
        """
        Call before any calls to :meth:`AddOffset`, :meth:`SetOffset`, :meth:`AddToMask` or :meth:`SetMask` if you wish it to be undone.

        .. warning::

            | This will only work if you are only making changes to a single layer.
            | Changes to multiple layers or layers at different levels is not allowed.

        .. note:

            You must be at the current subdivision level of the layer being changed for these calls to work properly.

        .. note::

            The method :meth:`EndUndo` must be called after all calls to the above functions have been done.
        """

    def EndUndo(self):
        """
        Must be called after :meth:`StartUndo` once all the points and masks have been changed on the layers.
        """

    def Smooth(self, count, respectMask):
        """
        Smooth the sculpt object and apply the offsets to the currently selected layer.

        :type count: int
        :param count: The number of times to run the smooth algorithm.
        :type respectMask: bool
        :param respectMask: **True** to not smooth any masked out points, **False** to apply it to every point.
        """

    def GetMaskCachePoint(self, id):
        """
        Gets the mask value from the mask cache.

        .. versionadded:: R16.021

        :type id: int
        :param id: The index of the point.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :rtype: float
        :return: The mask cache value.
        """

    def UpdateMask(self, fullUpdate):
        """
        Updates the mask on the sculpt object.

        .. versionadded:: R16.021

        :type fullUpdate: bool
        :param fullUpdate: Pass **True** to force a full update of the mask.
        """

    def InitOpenGL(self, bd):
        """
        Initializes the sculpt object for the given viewport for OpenGL use. Private.

        .. versionadded:: R16.021

        :type bd: c4d.BaseDraw
        :param bd: The viewport that is being updated. If **None** then the currently active view will be used.
        """

    def IsPointSelected(self, index):
        """
        | For use in the :meth:`SculptBrushToolData.FloodSelectedLayer` method to determine if a point should be moved or not.
        | When in Point Mode, and there is a selection, it returns **True** if a point is selected or **False** if the point is not selected. If there are no points selected it returns **True**.
        | When in Polygon Mode, and there is a selection, it returns **True** if a point on any of the selected polygons is selected or **False** if there is no point selected. If there are no polygons selected it returns **True**.
        | It returns **False** in all other cases.

        .. versionadded:: R16.021

        .. note::

            This method only works when the selected object being sculpted on is by a tool and is a Polygon Object without a :class:`SculptTag <c4d.modules.sculpting.SculptTag>`.

        :type index: int
        :param index: The index of the point.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :rtype: bool
        :return: **True** if the point was selected, **False** if not.
        """

    def IsPolygonSelected(self, index):
        """
        | For use in the :meth:`SculptBrushToolData.FloodSelectedLayer` method to determine if a point should be moved or not.
        | When in Polygon Mode, and there is a selection, it returns **True** if a point on any of the selected polygons is selected or **False** if there is no point selected.
        | If there are no polygons selected it returns **True**. It returns **False** in all other cases.

        .. versionadded:: R16.021

        .. note::

            This method only works when the selected object being sculpted on is by a tool and is a Polygon Object without a :class:`SculptTag <c4d.modules.sculpting.SculptTag>`.

        :type index: int
        :param index: The index of the polygon.
        :raise IndexError: If the polygon *index* is out of range : *0<=index<*:meth:`GetPolygonCount`.
        :rtype: bool
        :return: **True** if the polygon was selected, **False** if not.
        """

    def GetPolygon(self, index):
        """
        Gets the Polygon at the given *index*.

        .. versionadded:: R16.021

        :type index: int
        :param index: The index of the polygon.
        :raise IndexError: If the polygon *index* is out of range : *0<=index<*:meth:`GetPolygonCount`.
        :rtype: c4d.CPolygon
        :return: The Polygon if it was found, otherwise **None**.
        """

    def GetDisplayPolygonObject(self):
        """
        | Retrieves the Polygon Object that is currently being displayed in the viewport.
        | This is the internal Polygon Object and should never be changed.

        .. versionadded:: R16.021

        .. note::

            In :meth:`SculptBrushToolData.FloodSelectedLayer` calls it returns the same as :meth:`GetOriginalObject` when sculpting on a Polygon Object that have no :class:`SculptTag <c4d.modules.sculpting.SculptTag>`.

        :rtype: c4d.PolygonObject
        :return: The Polygon Object displayed in the viewport.
        """


class SculptModifierInterface(object):
    """
    This interface lets apply the affects of a sculpting modifier to any Polygon Object.

    It allows to use the same algorithms outside of the sculpting system itself and deform a Polygon Object using the same brush algorithms that the sculpt brushes use.

    .. versionadded:: R16.021

    .. seealso:: :maxongithub:`sculpt_modifier_deformer plugin example<plugins/py-sculpt_modifier_deformer_r16/sculpt_modifier_deformer_r16.pyp>` showing how to use :class:`SculptModifierInterface <c4d.modules.sculpting.SculptModifierInterface>` in a deformer implementation.
    """
    def Init(self, poly):
        """
        Initializes the interface so that you can apply modifiers to the given Polygon Object.

        :type poly: c4d.PolygonObject
        :param poly: The Polygon Object that you wish to apply modifiers to.
        :rtype: bool
        :return: **True** if successfully initialized.
        """

    def Clear(self):
        """
        | Clears the interface.
        | This will free up any internal data that was required to apply modifiers to the initialized :class:`PolygonObject <c4d.PolygonObject>` in :meth:`Init`.
        """

    def GetDefaultData(self):
        """
        Gets the default brush data setting. These settings can be found in `toolsculptbrushbase.h`.

        :rtype: c4d.BaseContainer
        :return: The container containing all the default brush settings.
        """

    def GetModifierCount(self):
        """
        Gets the number of available modifiers that are currently registered and able to be used.

        :rtype: int
        :return: The number of Modifiers.
        """

    def GetModifierInfo(self, index):
        """
        Gets the information about a modifier given its *index*.

        :type index: int
        :param index: The index into the list of available modifiers. :meth:`GetModifierCount` returns the number of modifiers.
        :rtype: dict{**id**: int, **name**: str}
        :return: The modifier information.
        """

    def SetData(self, brushData, modifierData):
        """
        | Sets the brush data and modifier data for the the next dab to be drawn.
        | This must be called before :meth:`ApplyModifier`. This will initialize any time consuming data before you make repeated calls to :meth:`ApplyModifier`.
        | Operations that take time are things such as enabling stamps, changing a stamps texture, calculation of the falloff values etc...

        :type brushData: c4d.BaseContainer
        :param brushData: The brush data settings. By default you can just use the container  returned by :meth:`GetDefaultData`.
        :type modifierData: c4d.BaseContainer
        :param modifierData:

            | The settings for the modifier itself. Each modifier is a :class:`BaseList2D <c4d.BaseList2D>` node and could have its own settings.
            | Refer to each modifiers BM file (`BMknife.h` as an example).

        :rtype: bool
        :return: **True** if the data was correctly set.
        """

    def ApplyModifier(self, modifierId, vertex, brushData, modifierData, respectselections=False):
        """
        Applies a modifier to the Polygon Object near the specified *vertex*.

        :type modifierId: int
        :param modifierId: The ID of the modifier to apply. This is retrieved from a call to :meth:`GetModifierInfo`.
        :type vertex: int
        :param vertex: The index of the vertex on the PolygonObject where you want to apply the modifier to.
        :type brushData: c4d.BaseContainer
        :param brushData: The brush data settings. By default you can just use the container  returned by :meth:`GetDefaultData`.
        :type modifierData: c4d.BaseContainer
        :param modifierData:

            | The settings for the modifier itself. Each modifier is a :class:`BaseList2D <c4d.BaseList2D>` node and could have its own settings.
            | Refer to each modifiers BM file (`BMknife.h` as an example).

        :type respectselections: bool
        :param respectselections: Pass **True** for the modifier to respect any polygon or point selections on the Polygon Object. Default to **False**.
        :rtype: bool
        :return: **True** if the modifier was successfully applied.
        """

    def ApplyModifierExact(self, modifierId, vertex, brushData, modifierData, hitpoint, lasthitpoint, respectselections=False):
        """
        Exactly applies a modifier to the Polygon Object near the specified *vertex* using the given *hitpoint*.

        :type modifierId: int
        :param modifierId: The ID of the modifier to apply. This is retrieved from a call to :meth:`GetModifierInfo`.
        :type vertex: int
        :param vertex: The index of the vertex on the PolygonObject where you want to apply the modifier to.
        :type brushData: c4d.BaseContainer
        :param brushData: The brush data settings. By default you can just use the container  returned by :meth:`GetDefaultData`.
        :type modifierData: c4d.BaseContainer
        :param modifierData:  | The settings for the modifier itself. Each modifier is a :class:`BaseList2D <c4d.BaseList2D>` node and could have its own settings.
                                                    | Refer to each modifiers BM file (`BMknife.h` as an example).
        :type respectselections: bool
        :param respectselections: Pass **True** for the modifier to respect any polygon or point selections on the Polygon Object. Default to **False**.
        :type hitpoint: c4d.Vector
        :param hitpoint: The exact hitpoint on the surface of a polygon that is connected to the passed *vertex*.
        :type lasthitpoint: c4d.Vector
        :param lasthitpoint:

            | The last hitpoint from the previous call to :meth:`ApplyModifier`.
            | This is used to determine the direction of the dab for modifiers such as the knife and pinch modifier.

        :rtype: bool
        :return: **True** if the modifier was successfully applied.
        """


class SculptLayerData(BaseList2D):
    """
    A :class:`SculptLayerData <c4d.modules.sculpting.SculptLayerData>` node contains all the offset data and mask data for that layer at its subdivision level.

    .. versionadded:: R15.037
    """
    def GetSubdivisionLevel(self):
        """
        Get the level that this layer contains data for.

        :rtype: int
        :return: The subdivision level.
        """

    def GetPointCount(self):
        """
        Get the number of points on the polygon object that this layer has.

        :rtype: int
        :return: Number of points on the polygon object.
        """

    def GetOffset(self, index):
        """
        Get the offset for the given point *index* on the layer.

        :type index: int
        :param index: Index of the point on the polygon object.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :rtype: c4d.Vector
        :return: The offset of the point.
        """

    def SetOffset(self, index, offset):
        """
        Set the offset for the given point *index*.

        .. note::

            | Be sure to call :meth:`SculptObject.Update` after all changes to the offets have been made.
            | This will update the :class:`SculptObject <c4d.modules.sculpting.SculptObject>` display.

        .. note:

            You will also need to call :meth:`SculptObject.UpdateCollision` if you intend on using :meth:`SculptObject.HitScreen` or :meth:`SculptObject.HitObject` afterwards.

        :type index: int
        :param index: Index of the point on the polygon object.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :type offset: c4d.Vector
        :param offset: The full offset to set.
        """

    def AddOffset(self, index, offset):
        """
        Add to the existing offset value at the given point *index*.

        .. note::

            | Be sure to call :meth:`SculptObject.Update` after all changes to the offsets have been made.
            | This will update the :class:`SculptObject <c4d.modules.sculpting.SculptObject>` display.

        .. note:

            You will also need to call :meth:`SculptObject.UpdateCollision` if you intend on using :meth:`SculptObject.HitScreen` or :meth:`SculptObject.HitObject` afterwards.

        :type index: int
        :param index: Index of the point on the polygon object.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :type offset: c4d.Vector
        :param offset: The offset to add.
        """

    def GetMask(self, index):
        """
        Get the value (between 0 and 1) of the mask at the given point *index*.

        :type index: int
        :param index: Index of the point on the polygon object.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :rtype: float
        :return: The mask value for the given point, or **None** if there was no mask value at that point.
        """

    def SetMask(self, index, mask):
        """
        Set the mask at the given point. The value will be clamped between 0 and 1.

        :type index: int
        :param index: Index of the point on the polygon object.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :type mask: float
        :param mask: The mask value to set.
        """

    def AddToMask(self, index, mask):
        """
        Adds the mask at the given point. The value will be clamped between 0 and 1.

        :type index: int
        :param index: Index of the point on the polygon object.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :type mask: float
        :param mask: The amount to add to the existing mask.
        """

    def HasMask(self):
        """
        Check if this Layer has a mask applied to it.

        :rtype: bool
        :return: **True** if if there is mask data, otherwise **False**.
        """

    def ClearMask(self):
        """
        Clear all the mask data for this layer.
        """

    def ClearLayer(self):
        """
        Clear all the offsets for this layer.
        """

    def InitializeAllPointData(self):
        """
        Make sure all the data has been allocated to store all the point data.

        .. note::

            If you are going to call :meth:`SetOffset` or :meth:`AddOffset` from multiple threads then the data needs to be initialized before these calls are made.

        .. note::

            If you are not using multiple threads the calls to :meth:`SetOffset` and :meth:`AddOffset` will only allocate data if required.
        """

    def InitializeAllMaskData(self):
        """
        Make sure all the data has been allocated to store all the mask data.

        .. note::

            If you are going to call :meth:`SetMask` or :meth:`AddToMask` from multiple threads then the data needs to be initialized before these calls are made.

        .. note::

            If you are not using multiple threads the calls to :meth:`SetMask` and :meth:`AddToMask` will only allocate data if required.
        """

    def TouchPointForUndo(self, index):
        """
        Mark the point so that any modifications to it can be undone.

        .. note::

            Must be called after :meth:`SculptObject.StartUndo`.

        .. warning::

            This method cannot be called from multiple threads.

        :type index: int
        :param index: The index of the point on the layer.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        """

    def TouchMaskForUndo(self, index):
        """
        Marks the masked point so that any modifications to the mask can be undone.

        .. note::

            Must be called after :meth:`SculptObject.StartUndo`.

        .. warning::

            This method cannot be called from multiple threads.

        :type index: int
        :param index: The index of the point on the layer.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        """


class SculptLayerBase(BaseObject):
    """
    .. versionadded:: R15.037
    """
    def Select(self):
        """
        Select the layer.

        .. note::

            This will only work if the subdivision level is at the same level as this layer.

        :rtype: bool
        :return: **True** if the layer was selected, otherwise **False**.
        """

    def IsVisible(self):
        """
        Check if the layer is currently visible on the sculpt object.

        :rtype: bool
        :return: **True** if visible, **False** if invisible.
        """

    def SetVisible(self, state):
        """
        Set the visibility of this layer on the sculpt object.

        :type state: bool
        :param state: The visibility state.
        """

    def IsLocked(self):
        """
        Check if the layer is currently locked on the sculpt object.

        :rtype: bool
        :return: **True** if locked, **False** if unlocked.
        """

    def SetLocked(self, state):
        """
        Set the locked status of the layer on the sculpt object.

        :type state: bool
        :param state: The locked state.
        """

    def GetStrength(self):
        """
        Get the currents strength of the layer.

        :rtype: float
        :return: The strength value.
        """

    def SetStrength(self, strength):
        """
        Set the strength of the layer on the sculpt object.

        :type strength: float
        :param strength: The strength value to set.
        """


class SculptLayer(SculptLayerBase):
    """
    A :class:`SculptLayer <c4d.modules.sculpting.SculptLayer>` can contain one or more :class:`SculptLayerData <c4d.modules.sculpting.SculptLayerData>` children.

    .. versionadded:: R15.037
    """

    def GetFirstSculptLayer(self):
        """
        | Get the first layer data for this layer.
        | The Base Object layer will have more than one, other layers only have 1.

        :rtype: c4d.modules.sculpting.SculptLayerData
        :return: The first sculpt layer data.
        """

    def GetCurrentSculptLayer(self):
        """
        Get the currently used layer data.

        .. note::

            | In the case of the Base Object layer it will get the data for the current subdivision level.
            | For all other layers it will return the same as :meth:`GetFirstSculptLayer`.

        :rtype: c4d.modules.sculpting.SculptLayerData
        :return: The current sculpt layer data.
        """

    def GetPointCount(self):
        """
        Get the number of points this layer has.

        .. note::

            The point count will be the same as the number of points on the :class:`PolygonObject <c4d.PolygonObject>` for the subdivision level that this layer is at.

        :rtype: int
        :return: The number of points.
        """

    def GetOffset(self, index):
        """
        Get the offset value for the point *index* on the layer. This method will get the correct :class:`SculptLayerData <c4d.modules.sculpting.SculptLayerData>` for this layer and call the corresponding method for it.

        :type index: int
        :param index: The index of the point on the layer.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :rtype: c4d.Vector
        :return: The offset of the point.

        """

    def SetOffset(self, index, offset):
        """
        Set the offset vector for the given point on the layer.

        .. note::

            This method will get the correct :class:`SculptLayerData <c4d.modules.sculpting.SculptLayerData>` for this layer and call the corresponding method for it.

        .. warning::

            | Be sure to call :meth:`SculptObject.Update` after all changes to the offets have been made.
            | This will update the :class:`SculptObject <c4d.modules.sculpting.SculptObject>` display.

        .. note:

            You will also need to call :meth:`SculptObject.UpdateCollision` if you intend on using :meth:`SculptObject.HitScreen` or :meth:`SculptObject.HitObject` aftewards.

        :type index: int
        :param index: The index of the point on the layer.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :type offset: c4d.Vector
        :param offset: The full offset to set.
        """

    def AddOffset(self, index, offset):
        """
        Add an offset vector to the existing offset for the given point on the layer.

        .. note::

            This method will get the correct :class:`SculptLayerData <c4d.modules.sculpting.SculptLayerData>` for this layer and call the corresponding method for it.

        .. warning::

            | Be sure to call :meth:`SculptObject.Update` after all changes to the offets have been made.
            | This will update the :class:`SculptObject <c4d.modules.sculpting.SculptObject>` display.

        .. note:

            You will also need to call :meth:`SculptObject.UpdateCollision` if you intend on using :meth:`SculptObject.HitScreen` or :meth:`SculptObject.HitObject` aftewards.

        :type index: int
        :param index: The index of the point on the layer.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :type offset: c4d.Vector
        :param offset: The offset to add.
        """

    def GetMask(self, index):
        """
        Get the mask value for the point (between 0 and 1).

        .. note::

            This method will get the correct :class:`SculptLayerData <c4d.modules.sculpting.SculptLayerData>` for this layer and call the corresponding method for it.

        :type index: int
        :param index: The index of the point on the layer.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :rtype: float
        :return: The mask value for the given point.
        """

    def SetMask(self, index, mask):
        """
        Set the mask value for the point (between 0 and 1).

        .. note::

            This method will get the correct :class:`SculptLayerData <c4d.modules.sculpting.SculptLayerData>` for this layer and call the corresponding method for it.

        :type index: int
        :param index: The index of the point on the layer.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :type mask: float
        :param mask: The mask value for the given point.
        """

    def AddToMask(self, index, mask):
        """
        Add to the existing mask value at this point (between 0 and 1).

        .. note::

            This method will get the correct :class:`SculptLayerData <c4d.modules.sculpting.SculptLayerData>` for this layer and call the corresponding method for it.

        :type index: int
        :param index: The index of the point on the layer.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :type mask: float
        :param mask: The value to add to the mask.
        """

    def HasMask(self):
        """
        Check if this layer has a mask at the current subdivision level.

        .. note::

            This method will get the correct :class:`SculptLayerData <c4d.modules.sculpting.SculptLayerData>` for this layer and call the corresponding method for it.

        :rtype: bool
        :return: **True** if there is a mask, otherwise **False**.
        """

    def ClearMask(self):
        """
        Clear the mask data for the layer.

        .. note::

            This method will get the correct :class:`SculptLayerData <c4d.modules.sculpting.SculptLayerData>` for this layer and call the corresponding method for it.
        """

    def ClearLayer(self):
        """
        Clear all the offset data for this layer.

        .. note::

            This method will get the correct :class:`SculptLayerData <c4d.modules.sculpting.SculptLayerData>` for this layer and call the corresponding method for it.
        """

    def InitializeAllPointData(self):
        """
        Make sure all the data has been allocated to store all the point data.

        .. note::

            If you are going to call :meth:`SetOffset` or :meth:`AddOffset` from multiple threads then the data needs to be initialized before these calls are made.

        .. note::

            If you are not using multiple threads the calls to :meth:`SetOffset` and :meth:`AddOffset` will only allocate data if required.
        """

    def InitializeAllMaskData(self):
        """
        Make sure all the data has been allocated to store all the mask data.

        .. note::

            If you are going to call :meth:`SetMask` or :meth:`AddToMask` from multiple threads then the data needs to be initialized before these calls are made.

        .. note::

            If you are not using multiple threads the calls to :meth:`SetMask` and :meth:`AddToMask` will only allocate data if required.
        """

    def TouchPointForUndo(self, index):
        """
        Mark the point so that any modifications to it can be undone.

        .. note::

            Must be called after :meth:`SculptObject.StartUndo`.

        .. warning::

            This method cannot be called from multiple threads.

        :type index: int
        :param index: The index of the point on the layer.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        """

    def TouchMaskForUndo(self, index):
        """
        Mark the masked point so that any modifications to the mask can be undone.

        .. note::

            Must be called after :meth:`SculptObject.StartUndo`.

        .. warning::

            This method cannot be called from multiple threads.

        :type index: int
        :param index: The index of the point on the layer.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        """

    def IsBaseLayer(self):
        """
        Check if this layer is the Base Object layer in which case it will have more than one :class:`SculptLayerData <c4d.modules.sculpting.SculptLayerData>` children.

        :rtype: bool
        :return: **True** if this layer is the Base Object layer, **False** if it is a regular layer.
        """

    def IsMaskEnabled(self):
        """
        Check if the mask is enabled for this layer at the current subdivision level.

        .. note::

            This method will get the correct :class:`SculptLayerData <c4d.modules.sculpting.SculptLayerData>` for this layer and call the corresponding method for it.

        :rtype: bool
        :return: *True** if mask is enabled, otherwise **False**.
        """

    def SetMaskEnabled(self, state):
        """
        Set the mask enabled *state* for the current layer data at this current subdivision level.

        .. note::

            This method will get the correct :class:`SculptLayerData <c4d.modules.sculpting.SculptLayerData>` for this layer and call the corresponding method for it.

        :type state: bool
        :param state: The state of the mask.
        """


class SculptFolder(SculptLayerBase):
    """
    A :class:`SculptFolder <c4d.modules.sculpting.SculptFolder>` can contain many :class:`SculptLayer <c4d.modules.sculpting.SculptLayer>` objects or other :class:`SculptFolder <c4d.modules.sculpting.SculptFolder>` objects as children.

    .. versionadded:: R15.037
    """
    pass


class SculptBrushParams(object):
    """
    The parameters to pass in when registering a Sculpting Brush.

    .. versionadded:: R16.021
    """
    def EnableStencil(self, enable):
        """
        | Does the brush use stencils?
        | Settings this to **False** will let the brush know that you are not going to be using stencils. This will free up some resource and computation time.
        | Note that setting to **False** will also remove the tab from the brush interface.

        :type enable: bool
        :param enable:

            | **True** if the brush uses stencils, otherwise **False**.
            | Default is **True**.
        """

    def EnableStamp(self, enable):
        """
        | Does the brush use stamps?
        | Setting this to **False** will let the brush know that you are not going to be using stamps. This will free up some resource and computation time.
        | Note that setting to **False** will also remove the tab from the brush interface.

        :type enable: bool
        :param enable: **True** if the brush uses stamps, otherwise **False**. Default is **True**.
        """

    def EnableInvertCheckbox(self, enable):
        """
        | Does the brush use the invert checkbox?
        | Lets the system know if you are using the invert checkbox or not.

        | Note that by default the invert checkbox is not part of the base `.res` file so you will need to add it yourself to your own brushes `.res` file.
        | To do this just add the following data to your .res file exactly as shown:

        .. code-block:: cpp

            GROUP MDATA_SCULPTBRUSH_SETTINGS_GROUP
            {
                COLUMNS 3;
                BOOL MDATA_SCULPTBRUSH_SETTINGS_INVERT { }
                STATICTEXT { DUMMY; }
                STATICTEXT { DUMMY; }
            }

        :type enable: bool
        :param enable:

            | **True** if the brush uses the invert checkbox, otherwise **False**.
            | Default is **False**.
        """

    def EnableBuildup(self, enable):
        """
        | Does the brush use the buildup slider?
        | Lets the system know if you are using the buildup slider or not.

        | Note that by default the buildup slider is not part of the base `.res` file so you will need to add it yourself to your own brushes `.res` file.
        | To do this just add the following data to your .res file exactly as shown:

        .. code-block:: cpp

            GROUP MDATA_SCULPTBRUSH_SETTINGS_GROUP
            {
                COLUMNS 3;
                REAL MDATA_SCULPTBRUSH_SETTINGS_BUILDUP { MIN 1; MAX 100; MINSLIDER 1; MAXSLIDER 100; CUSTOMGUI REALSLIDER; FIT_H; SCALE_H; }
                STATICTEXT { JOINENDSCALE; }
                STATICTEXT { JOINEND; }
            }

        :type enable: bool
        :param enable:

            | **True** if the brush uses the buildup slider, otherwise **False**.
            | Default is **False**.
        """

    def EnableNonModelPickMode(self, enable):
        """
        | Does the brush do anything if the user clicks off of a model?
        | I.e. have you implemented :meth:`SculptBrushToolData.HandleNonModelPickMode and :meth:`SculptBrushToolData.DrawNonModelPickMode`?
        | Private.

        :type enable: bool
        :param enable:

            | **True** if the brush has implemented :meth:`SculptBrushToolData.HandleNonModelPickMode` and :meth:`SculptBrushToolData.DrawNonModelPickMode`, otherwise **False**.
            | Default is **False**.
        """

    def EnableFlood(self, enable):
        """
        | Does the brush have a Flood function?
        | I.e. have you implemented FloodSelectedLayer.

        | Note that by default the Flood button is not part of the base `.res` file so you will need to add it yourself to your own brushes `.res` file.
        | To do this just add the following data to your .res file exactly as shown:

        .. code-block:: cpp

            GROUP MDATA_SCULPTBRUSH_SETTINGS_GROUP
            {
                COLUMNS 3;
                BUTTON MDATA_SCULPTBRUSH_SETTINGS_FLOOD{ }
                STATICTEXT { JOINENDSCALE; }
                STATICTEXT { JOINEND; }
            }

        :type enable: bool
        :param enable:

            | **True** if the brush has implemented a Flood function, otherwise **False**.
            | Default is **False**.
        """

    def EnableToolSpecificSmooth(self, enable):
        """
        | Does the brush have its own smooth operation that gets used when you press the shift key?
        | You can check for this in the :meth:`SculptBrushToolData.ApplyDab` method by checking if (GetBrushOverride() & *OVERRIDE_SMOOTHTOOL*) is **True** and then you can implement your own smooth method.
        | Otherwise it will use the Smooth Brush for smoothing.

        :type enable: bool
        :param enable: **True** if you are handling smoothing yourself, otherwise **False**. Default is **False**.
        """

    def EnableModifier(self, enable):
        """
        Tells the system that this brush can use modifiers from other brushes (display the modifiers tab).

        :type enable: bool
        :param enable: Set to **True** if you want this brush to be able to use modifiers from other brushes.
        """

    def EnableDrawDirection(self, enable):
        """
        | When enabled the Draw Direction UI will appear in the settings tab.
        | Calls can then be made to :meth:`BrushDabData.GetDrawDirectionNormal` to get the direction of the normal based on the currently selected Draw Direction.

        :type enable: bool
        :param enable: Set to **True** to display the Draw Direction UI. Disabled by default.
        """

    def EnableRespectSelections(self, enable):
        """
        When enabled will tell the brush to respect Point and Polygon selections when in Point or Polygon mode respectively.

        :type enable: bool
        :param enable:

            | **True** if the brush should respect selections, otherwise **False**.
            | Default is **False**.
        """

    def EnableFillToolIsolatedPointRemover(self, enable):
        """
        | When this is enabled it will tell the Fill algorithm to remove any isolated points. That is any points that are selected but have no neighboring selections.
        |
        | This can happen on high resolution meshes due to the nature of the hit detection against screen space pixels defined by the fill tools.
        | By setting this to **False** it will keep any isolated points that are selected.
        | This is set to **True** by default so isolated points are removed before being sent to the :meth:`SculptBrushToolData.ApplyDab` function.

        :type enable: bool
        :param enable:

            | **True** if the brush should remove isolated points, **False** if it should keep them.
            | Default is **True**.
        """

    def EnablePressureHUD(self, enable):
        """
        When enabled will display the pressure value in the sculpting size/pressure HUD.

        :type enable: bool
        :param enable:

            | **True** if the brush should dispay the pressure value, otherwise **False**.
            | Default is **True**.
        """

    def EnableBackfaceSculpting(self, enable):
        """
        Tells the system that this brush supports backface sculpting and that the backface option should be displayed in the brushes settings.

        .. versionadded:: R17.032

        :type enable: bool
        :param enable:

            | **True** if the brush supports backface sculpting, otherwise **False**.
            | Default is **False**.
        """

    def EnableMouseData(self, enable):
        """
        Enables/disables the callback for the :meth:`SculptBrushToolData.MouseData` method.

        .. versionadded:: R17.048

        :type enable: bool
        :param enable:

            | **True** if the brush needs the :meth:`SculptBrushToolData.MouseData` callback, otherwise **False**.
            | Default is **True**.
        """

    def SetFloodType(self, type):
        """
        Specifies what kind of data the flood operation will change (points or mask).

        :type type: int
        :param type: The flood data type. Default is *SCULPTBRUSHDATATYPE_POINT*.
        """

    def SetBrushMode(self, mode):
        """
        Specifies what type of brush this is (grab or normal).

        :type mode: int
        :param mode: The brush mode. Default is *SCULPTBRUSHMODE_NORMAL*.
        """

    def SetFirstHitPointType(self, type):
        """
        Specifies what should happen when the user first clicks on model before dragging.

        :type type: int
        :param type: The first hitpoint type. Default is *FIRSTHITPPOINTTYPE_SELECTED*.
        """

    def SetUndoType(self, type):
        """
        Specifies what kind of data the brush will be changing and storing in the undo system (point or mask).

        :type type: int
        :param type: The brush data type. Default is *SCULPTBRUSHDATATYPE_POINT*.
        """

    def SetPolygonObjectDirtyFlags(self, type):
        """
        | Sets which flags should be checked to do a rebuild of the collision structure for a :class:`PolygonObject <c4d.PolygonObject>`.
        | These flags are used to check against the PolygonObjects dirty flags when a stroke is about to be done on a :class:`PolygonObject <c4d.PolygonObject>`.
        | If the flags being checked are dirty since the last check then the collision cache structure for the object will be rebuilt.
        | This can be used in cases such as the Select Brush where you are not directly moving the points of the model during a stroke.
        | So you can set all the flags except the **DIRTYFLAGS_SELECT** - using something like **DIRTYFLAGS_ALL & ~DIRTYFLAGS_SELECT** - to ensure that the object is not recalculated when just the select flags are changed.
        | In all other cases the object will be rebuilt.

        .. versionadded:: R17.032

        :type type: int
        :param type: The dirty flags to check:

            .. include:: /consts/DIRTYFLAGS.rst
                :start-line: 3
        """


class BrushDabData(object):
    """
    The brush data for an individual dab.

    .. versionadded:: R16.021
    """
    def GetData(self):
        """
        Gets the settings data for the tool.

        :rtype: c4d.BaseContainer
        :return: The data.
        """

    def GetObject(self):
        """
        Gets the Sculpt Object that the dab is for.

        :rtype: c4d.modules.sculpting.SculptObject
        :return: The sculpt object.
        """

    def GetPointData(self, index):
        """
        Gets the point at *index* affected by the brush.

        :type index: int
        :param index: The index of the point.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :rtype: dict{**pointIndex**: int, **distance**: float}
        :return: The point data index and distance.
        """

    def GetPolyData(self, index):
        """
        Gets the polygon at *index* affected by the brush.

        :type index: int
        :param index: The index of the polygon.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPolyCount`.
        :rtype: dict{**polyIndex**: int, **distance**: float}
        :return: The polygon data index.
        """

    def GetPolygonObject(self):
        """
        Gets the Polygon Object for the Sculpt Object that is currently being displayed in the viewport.

        :rtype: c4d.PolygonObject
        :return: The Polygon Object.
        """

    def GetBaseObject(self):
        """
        Gets the original object that the Sculpt Tag is applied to.

        .. note::

            In the case where this there is no Sculpt Tag on then this will return the same as the call to :meth:`GetPolygonObject`.

        :rtype: c4d.PolygonObject
        :return: The original object.
        """

    def GetPointCount(self):
        """
        Gets the number of points that are touched by the dab.

        :rtype: int
        :return: The number of points.
        """

    def GetPolyCount(self):
        """
        Gets the number of polygons that are touched by the dab.

        :rtype: int
        :return: The number of polygons.
        """

    def GetNeighbor(self):
        """
        Gets the neighbor information for the Sculpt Object if it is currently at level `0`.

        .. note::

            If the user is sculpting a regular unsubdivided Polygon Object then this will also return a neighbor information.

        :rtype: c4d.utils.Neighbor
        :return: The Neighbor information if Sculpt Object is at level `0` (or if the user is sculpting on a regular :class:`PolygonObject <c4d.PolygonObject>`), otherwise **None**.
        """

    def GetLayer(self):
        """
        Retrieves the currently selected Layer for a subdivided :class:`SculptObject <c4d.modules.sculpting.SculptObject>`.

        .. note::

            If the user is sculpting a regular :class:`PolygonObject <c4d.PolygonObject>`) then this will return **None**.

        :rtype: c4d.modules.sculpting.SculptLayer
        :return: The currently selected layer in the LayerManager if it is a subdivided :class:`SculptObject <c4d.modules.sculpting.SculptObject>`, otherwise **None**.
        """

    def GetPoint(self, index):
        """
        | Retrieves the live point at *index* that is modified on the surface during a brush stroke.
        | This point may already have been modified by previous brush dabs during the current brush stroke.

        :type index: int
        :param index: The index of the point.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :rtype: c4d.Vector
        :return: The point at *index* on the :class:`PolygonObject <c4d.PolygonObject>` that is currently displayed in the viewport.
        """

    def GetOriginalPoint(self, index):
        """
        Retrieves a copy of the point at *index* in its state before the brush stroke started.

        .. note::

            | You can use this point to compare where the surface was before the user started sculpting.
            | As an example this data is used by the grab tool to correctly offset the points based on their original location on the surface at the first mouse click.

        :type index: int
        :param index: The index of the point.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :rtype: c4d.Vector
        :return: The point at *index*  of the PolygonObject at the state it was in when the user first pressed the left mouse button down.
        """

    def GetNormal(self):
        """
        | Gets the normal at the current hitpoint for the dab.
        | This is the average vertex normal of all the points that are affected by the dab.

        :rtype: c4d.Vector
        :return: The normal at the current hitpoint.
        """

    def GetDrawDirectionNormal(self):
        """
        | If the brush supports the Draw Direction, i.e. the user has set :meth:`SculptBrushParams.EnableDrawDirection` to **True**, then this returns the direction selected by the user.
        | Otherwise it just returns the same vector as :meth:`GetNormal`.

        :rtype: c4d.Vector
        :return: The Draw Direction normal.
        """

    def GetBrushStrength(self):
        """
        Gets the brush strength for the dab.

        .. warning::

            | This strength is not the same as the strength in the :class:`BaseContainer <c4d.BaseContainer>` data.
            | This also takes into account many other variables including tablet pressure to create the value.

        :rtype: float
        :return: The strength of the brush.
        """

    def GetBrushRadius(self):
        """
        Gets the brush radius for the dab. The size of the radius is in the Sculpt Object local space.

        .. warning::

            | This is not the same as the brush size in the :class:`BaseContainer <c4d.BaseContainer>` data.
            | This also takes into account other factors such as the distance from the camera and scale of the object and tablet values to determine the correct brush radius.

        :rtype: float
        :return: The radius of the brush.
        """

    def GetMousePos3D(self):
        """
        If the brush mode is *SCULPTBRUSHMODE_GRAB* then this method can be used to get the location of the mouse pointer in world space in the scene.

        :rtype: c4d.Vector
        :return: The position of the mouse in world space if the brush mode is *SCULPTBRUSHMODE_GRAB*, otherwise it returns :class:`c4d.Vector(0,0,0) <c4d.Vector>`.
        """

    def GetHitPoint(self):
        """
        Gets the point on the surface of the SculptObject where the dab is going to be placed. This is the center of the dab.

        .. note::

            If the mode is set to *SCULPTBRUSHMODE_GRAB* then this always returns the initial hit point that occurred when the user first pressed the left mouse button down.

        :rtype: c4d.Vector
        :return: The hitpoint on the surface.
        """

    def GetLastHitPoint(self):
        """
        Gets the hit point for the previous dab during the stroke.

        :rtype: c4d.Vector
        :return: The last hitpoint on the surface.
        """

    def GetHitPolygon(self):
        """
        | Gets the index of the polygon on the surface of the SculptObject where the dab is going to be placed.
        | This is the center of the dab.

        .. versionadded:: R17.032

        :rtype: int
        :return: The index of the polygon on hit the surface.
        """

    def GetEyePoint(self):
        """
        | Gets the location of the mouse in local space above the model.
        | This point is created by interpolating between previous and next real mouse hitpoint on the surface of the Sculpt Object.
        | It is then projected down onto the surface of the model to get the real hitpoint for this interpolated value.

        :rtype: c4d.Vector
        :return: The virtual mouse location in local space above the surface of the :class:`SculptObject <c4d.modules.sculpting.SculptObject>`.
        """

    def IsMirroredDab(self):
        """
        Checks if this dab is for a mirrored brush stroke.

        :rtype: bool
        :return: **True** if it's a mirrored dab or **False** if it's the main brush stroke.
        """

    def GetBrushOverride(self):
        """
        Gets the override flags. This could be any combination of the *OVERRIDE* flags.

        :rtype: int
        :return: The overrides if there are any or `0` if there are none.
        """

    def GetBaseDraw(self):
        """
        Gets the :class:`BaseDraw <c4d.BaseDraw>` that the user is currently drawing in.

        :rtype: int
        :return: The :class:`BaseDraw <c4d.BaseDraw>`.
        """

    def GetAveragePointAndNormal(self):
        """
        | Gets the average point and normal.
        | Depending on what the Fixed Plane (*MDATA_SCULPTBRUSH_SETTINGS_FIXEDPLANE*) setting is for the brush this will return one of `3` things:

        - *MDATA_SCULPTBRUSH_SETTINGS_FIXEDPLANE_OFF*
            - averagePoint = The average location of all the points that are touched by the dab.
            - normal = The normal at the hitpoint on the surface of the Sculpt Object.
        - *MDATA_SCULPTBRUSH_SETTINGS_FIXEDPLANE_MOUSEDOWN*
            - averagePoint = The average location of all the points under the dab area when the mouse was mouse button was first pressed.
            - normal = The average normal of all the points under the dab area when the mouse was mouse button was first pressed.
        - *MDATA_SCULPTBRUSH_SETTINGS_FIXEDPLANE_WORKPLANE*
            - averagePoint = The point on the workplane that is above the hitpoint on the surface of the Sculpt Object.
            - normal = The normal of the workplane.

        :rtype: dict{**averagePoint**: :class:`Vector <c4d.Vector>`, **normal**: :class:`Vector <c4d.Vector>`}
        :return: The average point and normal based on the Fixed Plane setting.
        """

    def GetMirrorPoint(self, point, isNormal):
        """
        | Mirror the point (or Normal) from the objects space to the correct location for the current dab.
        | This should only be used if you need to get the symmetrically mirrored point for a point that you specifically need.
        | In most cases this method would never be used because the brush system automatically handles symmetrical points for you.

        :type point: c4d.Vector
        :parameter point: The input point, or normal to mirror.
        :type isNormal: bool
        :parameter isNormal: Set to **True** if *point* is a normal, so that it will then only be rotated and will not be offset.
        :rtype: c4d.Vector
        :return: The mirrored point.
        """

    def ApplySmooth(self):
        """
        Applies an effect of the smooth brush to the current dab.

        .. note::

            Call this after you have modified the dab to smooth it out if needed.
        """

    def GetVertexNormal(self, index):
        """
        Gets the vertex normal at *index* for the Sculpt Object.

        :type index: int
        :param index: The index of the vertex.
        :raise IndexError: If the vertex *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :rtype: c4d.Vector
        :return: The vertex normal.
        """

    def GetOriginalVertexNormal(self, index):
        """
        Gets the state of a vertex normal before the user started a brush stroke.

        .. versionadded:: R17.048

        :type index: int
        :param index: The index of the vertex.
        :rtype: c4d.Vector
        :return: The original vertex normal.
        """

    def GetFaceNormal(self, index):
        """
        Gets the face normal at *index* for the SculptObject.

        .. versionadded:: R17.032

        :type index: int
        :param index: The index of the face.
        :rtype: c4d.Vector
        :return: The face normal.    """

    def GetAutoScaleValue(self, noRadius):
        """
        Returns a value which represents the scale of the Sculpt Object.

        .. note::

            | This can be used to convert a distance in object space with the value returned from :meth:`GetBrushRadius` to help adjust
            | the algorithm for your brush since the value returned from :meth:`GetBrushRadius` is also already adjusted using the same value.

        :type noRadius: bool
        :param noRadius: **True** means it will not take into account the radius of the object in its calculation and will only use the scale.
        :rtype: float
        :return: The scale value with which to adjust your local space vector or distance value.
        """

    def GetBrushFalloff(self, index, customDistance=-1.0):
        """
        | Returns the brush falloff for the point specified by the *index* value.
        | The falloff is already adjusted by using the values from the stamp and stencil so it can be used directly to adjust the strength of an offset that you wish to add to the layer.
        | Internally this method will use the distance that this point is from the hitpoint in its calculation. Pass in a value to *customDistance* to use a different distance.

        :type index: int
        :param index: The point data index returned from :meth:`GetPointData`.
        :type customDistance: float
        :param customDistance: The custom distance to use instead of the points actual distance from the hitpoint.
        :rtype: float
        :return: The final falloff value that can be used to adjust the offset value.
        """

    def GetBrushFalloffFromPos(self, pos):
        """
        Returns the falloff value, defined by the falloff curve, based on the distance from *pos* to the hitpoint for the dab.

        :type pos: c4d.Vector
        :parameter pos: A point in 3D space to get the falloff for.
        :rtype: float
        :return: The falloff value.
        """

    def OffsetPoint(self, index, offset, respectStrength=0):
        """
        Offsets the point on the layer by the given *offset* amount.

        .. note::

            This method should be used if :meth:`IsPreviewDab` returns **False**, otherwise use :meth:`OffsetPreviewPoint` instead.

        :type index: int
        :param index: The index of the point.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :type offset: c4d.Vector
        :param offset: The vector to offset the point by.
        :type respectStrength: int
        :param respectStrength:

            | Let you use or ignore settings such as the layers mask or strength when offsetting the point. See *SCULPTOFFSETFLAGS*.
            | By setting the *SCULPTOFFSETFLAGS_IGNOREMASK* flag it will ignore whatever the mask checkbox state is for the layer.
            | Otherwise it uses this state to determine if it should use the mask.
        """

    def IsPreviewDab(self):
        """
        Checks if this is a preview dab. Currently only DragDab and DragRect draw modes support preview brushes.

        :rtype: bool
        :return: **True** if it is a preview dab, otherwise **False**.
        """

    def OffsetPreviewPoint(self, index, offset):
        """
        | If :meth:`IsPreviewDab` returns **True** then you should apply your offset using this method.
        | If it returns **False** then you should use :meth:`OffsetPreviewPoint` instead.
        | This adds the offset to a temporary preview layer that is created when using the DragDab and DragRect draw modes.

        :type index: int
        :param index: The index of the point.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :type offset: c4d.Vector
        :param offset: The vector to offset the point by.
        """

    def DirtyAllPoints(self, flags):
        """
        Dirty all the points for this dab according to the flags.

        :type flags: int
        :param flags: See *SCULPTBRUSHDATATYPE*.
        """

    def IsPointModified(self, index):
        """
        | When using symmetry another mirrored brush may change the point.
        | You can use this to check if another brush stroke has changed a point and if so then you can do something different for this current stroke.

        :type index: int
        :param index: The index of the point.
        :raise IndexError: If the point *index* is out of range : *0<=index<*:meth:`GetPointCount`.
        :rtype: bool
        :return: **True** if the point was modified, otherwise **False**.
        """

    def GetStencilColor(self, point, mode=0):
        """
        Retrieves the grey value, color and coordinates of the stencil for a point in the Sculpt Object local space.

        :type point: int
        :param point: The index of the point.
        :raise IndexError: If the *point* index is out of range : *0<=index<*:meth:`GetPointCount`.
        :type mode: Optional[int]
        :param mode: The mode used to sample the stencil texture. See *SAMPLEMODE*.
        :rtype: dict{**grey**: :class:`Vector <c4d.Vector>`, **color**: :class:`Vector <c4d.Vector>`, **coords**: :class:`Vector <c4d.Vector>`}
        :return: The grey value, color and coords of the stencil.
        """

    def GetStampColor(self, point, distance, mode):
        """
        Retrieves the grey value, color and coordinates of the stamp for a point in the Sculpt Object local space.

        :type point: int
        :param point: The index of the point.
        :raise IndexError: If the *point* index is out of range : *0<=index<*:meth:`GetPointCount`.
        :type distance: float
        :param distance:

            | Can be either the point data distance value (returned by ::meth:`GetPointData`), the length of the vector (hitpoint - point) or a custom distance value.
            | This is used to get the correct falloff for the point.

        :type mode: int
        :param mode: The mode used to sample the stamp texture. See *SAMPLEMODE*.
        :rtype: dict{**grey**: :class:`Vector <c4d.Vector>`, **color**: :class:`Vector <c4d.Vector>`, **coords**: :class:`Vector <c4d.Vector>`}
        :return: The grey value (adjusted by the stamps Gray Value), color and coordinates of the stamp.
        """

    def GetStencil(self):
        """
        Retrieves the stencil bitmap used for this dab.

        :rtype: c4d.bitmaps.BaseBitmap
        :return: The bitmap for the stencil.
        """

    def GetStamp(self):
        """
        Retreves the stamp bitmap used for this dab.

        :rtype: c4d.bitmaps.BaseBitmap
        :return: The bitmap for the stamp.
        """

    def GetStrokeInstanceID(self):
        """
        Gets the ID of the stroke instance that this dab is being drawn for.

        :rtype: int
        :return: The stroke instance ID.
        """

    def IsSculptObject(self):
        """
        Checks if the object being touched is a :class:`SculptObject <c4d.modules.sculpting.SculptObject>` (i.e. has a :class:`SculptTag <c4d.modules.sculpting.SculptTag>`).

        :rtype: bool
        :return: **True** if the object being touched is a :class:`SculptObject <c4d.modules.sculpting.SculptObject>`, otherwise **False**.
        """

    def IsFillTool(self):
        """
        | Checks if the current draw mode is fill.
        | Basically checks if the dab *MDATA_SCULPTBRUSH_SETTINGS_DRAWMODE* setting is:
        | *MDATA_SCULPTBRUSH_SETTINGS_DRAWMODE_LASSO_FILL* or
        | *MDATA_SCULPTBRUSH_SETTINGS_DRAWMODE_POLY_FILL* or
        | *MDATA_SCULPTBRUSH_SETTINGS_DRAWMODE_RECTANGLE_FILL*

        :rtype: bool
        :return: **True** if the current draw mode is fill, otherwise **False**.
        """

    def IsBackface(self):
        """
        Returns **True** if the dab is being applied backfacing polygons.

        .. versionadded:: R17.032

        .. note::

            Backface polygons will only be sculpted on if the brush has its BackFaceSculpting option enabled and the Backface option is also checked by the user.

        :rtype: bool
        :return: **True** if the dab is on backfacing polygons, otherwise **False**.
        """
