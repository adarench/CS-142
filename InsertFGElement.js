/*
 
 ADOBE CONFIDENTIAL
 ___________________
 
 Copyright 2012 Adobe Systems Incorporated
 All Rights Reserved.
 
 NOTICE:  All information contained herein is, and remains
 the property of Adobe Systems Incorporated and its suppliers,
 if any.  The intellectual and technical concepts contained
 herein are proprietary to Adobe Systems Incorporated and its
 suppliers and are protected by trade secret or copyright law.
 Dissemination of this information or reproduction of this material
 is strictly forbidden unless prior written permission is obtained
 from Adobe Systems Incorporated.
 
 */

//---------------   GLOBAL VARIABLES   ---------------
var helpDoc = MM.HELP_objFluidElement;
var LIST_CLASSES;
var LIST_IDS;
var allClasses;
var allUnusedIDs;
var classesPopulated = false;
var idsPopulated = false;
var isInsertOptionsDisabled = false; 
var gridContainerDetailCache = null;
var insertOption = null; //values can be- before / after/ wrap/ nest
var COLORS = {
    WIN_DLG_BG : '#F0F0F0',
	MAC_DLG_BG : '#D6D6D6',
	HOVER      : '#727272'
};

elementCSSType ={
	NONE : 0,
	ID : 1,
	CLASS : 2
}

//---------------     API FUNCTIONS    ---------------

function isDOMRequired()
{
	return false;
}

function commandButtons()
{
   return new Array( MM.BTN_OK,     "doInsertDiv()",
                     MM.BTN_Cancel, "window.close()",
                     MM.BTN_Help,   "displayHelp()");
}

//---------------    LOCAL FUNCTIONS   ---------------

function mouseOverImage(element,imageName)
{
	if(isInsertOptionsDisabled)
	   return;
	updateInsertIcons();
	element.setAttribute('style', 'border: 1px '+COLORS.HOVER +';');
	if( insertOption === imageName)
	{
		return;
	}
	element.src = "insertFGIcons/insert_"+imageName+"_Over.png";
}

function mouseOutImage(element,imageName)
{
	if(isInsertOptionsDisabled)
	   return;
	var bgColor = COLORS.MAC_DLG_BG;
    if(dwscripts.IS_WIN)
        bgColor = COLORS.WIN_DLG_BG;
	if(insertOption!==imageName)
	{
		element.src = "insertFGIcons/insert_"+imageName+".png";
		element.style.border = "1px "+bgColor +";";
	}
	else
	{
		element.setAttribute('style', 'border: 1px '+COLORS.HOVER+';');
	}
}

function setInsertOption(option)
{
	if(isInsertOptionsDisabled)
	   return;
	insertOption = option;
	updateInsertIcons();
}

function updateInsertIcons()
{
    var suffix = "";
	if(isInsertOptionsDisabled)
		suffix = "_Disabled";
	var optionList = ['before','after','nest','wrap'];
	var bgColor = COLORS.MAC_DLG_BG;
    if(dwscripts.IS_WIN)
        bgColor = COLORS.WIN_DLG_BG;
	for (var i = 0; i < optionList.length; i++) 
	{
	    prefix = optionList[i];
		var optionImage = document.getElementById(prefix+"image");
		if(insertOption===prefix && !isInsertOptionsDisabled)
		{
			optionImage.src="insertFGIcons/insert_"+prefix+"_Down.png" ;
			optionImage.setAttribute('style', 'border: 1px '+COLORS.HOVER+';');
		}
		else
		{
			optionImage.src="insertFGIcons/insert_"+prefix+suffix+".png" ;
			optionImage.setAttribute('style', 'border: 1px '+bgColor+';');
		}
	}
	return;
}

function setFocusforIDField()
{
	document.forms[0].fgEleClass.disabled = true;
	document.forms[0].fgEleID.disabled = false;
	// There is timing issue(#3436218) in OSX 10.8, due to which focus is not applied 
	// since enabling the textbox is taking sometime. fixing this using a timer
	window.setTimeout(setFocusToText, 100);
}
function setFocusForClassField()
{
	document.forms[0].fgEleClass.disabled = false;
	document.forms[0].fgEleID.disabled = true;
	document.forms[0].fgEleClass.focus();
}
function setFocusToText()
{
	document.forms[0].fgEleID.focus();	
}
function FindOneOf(str, set)
{
	var strlen = str.length;
	var setlen = set.length;
	var i = 0;
	var j = 0;
	for(i=0; i< setlen; i++)
	{
		for(j = 0; j<strlen; j++)
		{
			if(str.charAt(j) == set.charAt(i))
			{
				return true;
			}
		}
	}
	return false;
}

function showError(msg)
{
	var eleTable = document.getElementById("errorTable");
	if (eleTable)
		eleTable.style.display = "block";
	var ele = document.getElementById("errMsg");
	if (ele)
		ele.innerHTML = msg;
}

function hideError()
{
	var eleTable = document.getElementById("errorTable");
	if (eleTable)
		eleTable.style.display = "none";
	var ele = document.getElementById("errMsg");
	if (ele)
		ele.innerHTML = "";
}

function validateString(str)
{
	var notAllowedSet = ".,?/\\'\"|][}{=+)(*&^%$#@!~`"; // this list i got from renameClass.cpp

	if(FindOneOf(str[0], "0123456789"))
	{
		var msg = dw.loadString("fgClassIdName/error/startingWithNumber");//"space not allowed"
		showError(msg);
		return false;
	}
	else if(str[0] == '-' && (str.length == 1 || FindOneOf(str[1], "0123456789-"))) //if starting with '-', check second char
	{
		var msg = dw.loadString("fgClassIdName/error/specialCharsNotAllowed");//"special chars not allowed"
		showError(msg);
		return false;
	}
	else if(str.search(" ") > -1)
	{
		var msg = dw.loadString("fgClassIdName/error/spacesNotAllowed");//"space not allowed"
		showError(msg);
		return false;
	}	
	else if(FindOneOf(str, notAllowedSet ))	
	{
		var msg = dw.loadString("fgClassIdName/error/specialCharsNotAllowed");//"special chars not allowed"
		showError(msg);
		return false;
	}
	return true;
}

function trimDefaultSelectorList(selectorList)
{
	// This list has to be updated whenever more standard Fluidgrid classes are added 
    var preDefClasses = new Array(".fluid", ".fluidList", ".gridContainer", ".hide_mobile", ".hide_tablet", ".hide_desktop", ".ie6", ".zeroMargin_mobile", ".zeroMargin_tablet", ".zeroMargin_desktop");
    var idx;
	for(idx = 0; idx < preDefClasses.length; idx++) 
    {
        var index = selectorList.indexOf(preDefClasses[idx]);
        if (index >= 0)
        {
            selectorList.splice(index, 1);            
        }
    }   
}

function populateClassList()
{
	//alert('populateClassList');	
	if (classesPopulated)
		return;

	var dom = dw.getDocumentDOM();
	if (dom)
	{
	    allClasses = dom.getSelectorsDefinedInFluidGridStylesheet('class');
	    trimDefaultSelectorList(allClasses);
		for (i = 0; i < allClasses.length; i++)
		{
			if (allClasses[i][0] == '.')
				allClasses[i] = allClasses[i].slice(1);
		}
		LIST_CLASSES.setAll(allClasses);
	}

	classesPopulated = true;
}

function populateIDList()
{
	//alert('populateIDList');	
	if (idsPopulated)
		return;

	var dom = dw.getDocumentDOM();
	if (dom)
	{
		var ids = dom.getSelectorsDefinedInStylesheet('id');
		allUnusedIDs = new Array();
		for (i = 0; i < ids.length; i++)
		{
			if (ids[i][0] == '#')
				ids[i] = ids[i].slice(1);
			if (!isIDInUse(ids[i]))
				allUnusedIDs.push(ids[i]);
		}
		LIST_IDS.setAll(allUnusedIDs);
	}
	idsPopulated = true;
}

function initializeFGUI()
{
	//alert('initializeUI');	
	var i;
	var dom = dw.getDocumentDOM();
	
	LIST_CLASSES = new ListControl('fgEleClass');
	LIST_IDS = new ListControl('fgEleID');

	LIST_CLASSES.setIndex(-1);
	LIST_IDS.setIndex(-1);		// we need this to verify for duplicate before updating the CSS

	populateClassList();
	
	if (dw.getPreferenceString("CSS Layout Framework Preferences", "Insert Fluid Element", "TRUE") == 'TRUE')
	{
		document.theForm.fgElement.checked = true;
	} else {
		document.theForm.fgElement.checked = false;
	}
	gridContainerDetailCache = getGridContainerDetailsForSelection();
	setupKeyFocusChains();
	toggleFGInputs();
}

function setupKeyFocusChains()
{
	var tabOrder = ['selectClass','elementClass','selectID','elementID','beforebutton','afterbutton','nestbutton'];
	for(var i=0; i<tabOrder.length; i++)
	{
		if(document.getElementById(tabOrder[i])!== undefined)
			document.getElementById(tabOrder[i]).tabIndex = i;	
	}
}

function toggleFGInputs()
{
	if((dw.getFocus(false) === 'textView') ||
		gridContainerDetailCache.bodySelected ||
	   (!gridContainerDetailCache.isSelectionInsideGridContainer && document.theForm.fgElement.checked) )
		isInsertOptionsDisabled = true;
	else
		isInsertOptionsDisabled = false;
    updateInsertIcons();
	if (document.getElementById('selectClass').checked)
		setFocusForClassField();
	else
		setFocusforIDField();
}

function isIDInUse(idStr)
{
	//alert('isIDInUser');	
	var dom = dw.getDocumentDOM();
	if (dom)
	{	
		var nodeList = dom.getElementsByAttributeName('id');
		if (nodeList)
		{
			for (var i = 0; i < nodeList.length; i++)
			{
			  var nodeId = nodeList[i].getAttribute('id');
				if (nodeId && (nodeId.toLowerCase() == idStr.toLowerCase()))
					return true;
			}
		}
	}
	return false;
}
	
function doInsertDiv()
{
	//alert('doInsertDiv');
	var tagName = document.getElementById("tagname").value;
	var dom = dw.getDocumentDOM();
	
	var cssType;
	var cssSelectorName;
	
	if (dom)
	{
		if(document.getElementById('selectID').checked)
		{
			cssSelectorName =document.forms[0].fgEleID.value;
			cssType = elementCSSType.ID;
			dw.logEvent(UT_FLUID_GRID, UT_FLUID_GRID_ELEMENT_INSERTED_WITH_ID);
		}		
		else if(document.getElementById('selectClass').checked)
		{
			cssSelectorName = LIST_CLASSES.get();
			cssType = elementCSSType.CLASS;
			dw.logEvent(UT_FLUID_GRID, UT_FLUID_GRID_ELEMENT_INSERTED_WITH_CLASS);
		}
	}
	
	if(cssSelectorName == '' && document.theForm.fgElement.checked)
	{	
		var msg = dw.loadString("insertbar/div/fgEmptyID");		
		showError(msg);
		return;
	}
	
	if(!isInsertOptionsDisabled && insertOption === null)
	{	
		var msg = dw.loadString("insertbar/div/insertWhereMissing");		
		showError(msg);
		return;
	}
	
	if(document.theForm.fgElement.checked && !validateString(cssSelectorName))
	{
		return;
	}

	if (cssType == elementCSSType.ID && isIDInUse(cssSelectorName))
	{
		var msg = dw.loadString("insertbar/div/fgDupID");
		showError(msg);
		return;
	}
	
	if (!document.theForm.fgElement.checked)
	{
	    // non fluid grid simple divs or other elements
		tagName = tagName.toLowerCase();
		var content = '';
		if (tagName == 'figure') {
			var figureContent = dw.loadString('Objects/layout/figure/defaultNonFluidContent');
			content = dw.loadString('Objects/layout/figcaption/defaultContent');
			content = figureContent + '<figcaption>' + content + '</figcaption>';
		}
		else {
			content = dw.loadString('Objects/layout/' + tagName + '/defaultNonFluidContent');
		}
		var cssTypeName = 'id';
		if (cssType == elementCSSType.CLASS)
		{
			cssTypeName = 'class';
		}
		if(cssSelectorName === '')
		   var html = '<' + tagName + '>' + content + '</' + tagName + '>';
		else
		   var html = '<' + tagName + ' ' + cssTypeName+ '="' + cssSelectorName + '">' + content + '</' + tagName + '>';

	    insertHTMLElement(html,false/*not fluid*/);
		
		dw.setPreferenceString("CSS Layout Framework Preferences", "Insert Fluid Element", "FALSE");
		
		window.close();
		return;
	}
		
	if (dw.getPreferenceString("CSS Layout Framework Preferences", "Insert Fluid Element", "TRUE") != 'TRUE') {
		dw.setPreferenceString("CSS Layout Framework Preferences", "Insert Fluid Element", "TRUE");
	}

	var newStyleSheetManager = new CssGrids.StyleSheetManager(dw,
									dw.getActiveWindow(),
									dwscripts,
									DWfile,
									new StyleSheet(dw)
								);

	insertFluidElement(tagName, cssSelectorName, cssType, newStyleSheetManager);

	window.close();
}


if (typeof CssGrids == 'undefined') CssGrids = {}; // Create our namespace

CssGrids.FluidGridLayoutElement = function (elementName, inDw, inDwscripts, inStyleSheetManager) {

	var self = this;

	self.publicFunctions = [
		'insert'
	];

	self.refs = {
		dw: inDw,
		dwscripts: inDwscripts,
		styleSheetManager: inStyleSheetManager
	};

	self.consts = {
		elementName: elementName
	};

	self.insert = function (cssSelector, cssType) {
		if (!self.refs.styleSheetManager.loadGridProps()) {
			// Style Sheet Manager will report error for us.
			return;
		}
		
		var cssChar = '#';
		var cssTypeName = 'id';
		if (cssType == elementCSSType.CLASS)
		{
			cssChar = '.';
			cssTypeName = 'class';
		}
		// Insert html and css.			
		var html = self.getHtmlToInsert(cssSelector, cssTypeName);
		var dom = self.refs.dw.getDocumentDOM();
        
		insertHTMLElement(html,true);
			
		if( ((elementCSSType.CLASS == cssType) && !LIST_CLASSES.find(cssSelector))
		||	((elementCSSType.ID == cssType) && !LIST_IDS.find(cssSelector))
		)
		{
            self.refs.styleSheetManager.insertRule(cssChar + cssSelector); // insert css after html is inserted
		}
	}

	self.getHtmlToInsert = function (cssSelector, cssTypeName) {
		var content = '';
		if (elementName == 'figure') {
			var figureContent = dw.loadString('Objects/layout/figure/defaultFluidContent');
			content = self.refs.dw.loadString('Objects/layout/figcaption/defaultContent');
			content = figureContent + '<figcaption>' + content + '</figcaption>';
		}
		else {
			content = self.refs.dw.loadString('Objects/layout/' + elementName + '/defaultFluidContent');
		}
		content = self.refs.dwscripts.sprintf(content, cssSelector);
		var cssClassFluid = 'fluid ';
		if(elementName.toLowerCase() === 'ul' || elementName.toLowerCase() === 'ol')
			  cssClassFluid = 'fluid fluidList ';
		if (cssTypeName === 'class') {
			cssSelector = cssClassFluid + cssSelector;
			return '<' + elementName + ' ' + cssTypeName+ '="' + cssSelector + '">' + content + '</' + elementName + '>';
		}
		else {
			return '<' + elementName + ' ' + cssTypeName+ '="' + cssSelector + '" class="'+cssClassFluid+'">' + content + '</' + elementName + '>';
		}
	}
}

function getGridContainerDetailsForSelection() {
    var details = {};
	var dom = dw.getDocumentDOM();
	var gridContainers = dom.getElementsByClassName("gridContainer clearfix");
	var offsets = dom.getSelection();
	details.isSelectionInsideGridContainer = false;
	if (dom.getSelectedNode()===dom.body)
	{
		details.bodySelected = true;
	}
	if(gridContainers.length > 0)
	{
		var gridContainerToInsertOffsets = dom.nodeToOffsets(gridContainers[gridContainers.length - 1]);
		var NearestGridContainerFound = false;
		for( index in gridContainers)
		{
			var gridContainerOffsets = dom.nodeToOffsets(gridContainers[index]);
			if((dom.getSelectedNode()===gridContainers[index]) ||
			   (offsets[1] <= gridContainerOffsets[0] && !NearestGridContainerFound) ||
			   (offsets[0] >= gridContainerOffsets[1] && !NearestGridContainerFound))
			{
				gridContainerToInsertOffsets = gridContainerOffsets;
				NearestGridContainerFound = true;
				details.NearestGridConatiner = gridContainers[index];
				details.isSelectionInsideGridContainer = false;
				break;
			}
			if((offsets[0] > gridContainerOffsets[0]) && (offsets[1] < gridContainerOffsets[1]))  // the gridContainer contains the selected offset
			{
				details.NearestGridConatiner = gridContainers[index];				
				details.isSelectionInsideGridContainer = true;
				break;
			}
			else if( (offsets[0] < gridContainerOffsets[0]) && (offsets[1] > gridContainerOffsets[1]))     // the selected offsets contains the grid container
			{
				details.NearestGridConatiner = gridContainers[index];				
				details.isSelectionInsideGridContainer = false;
				break;
			}
		}
	}
	return details;
}

function insertHTMLAtIP(html) {
	var domSource =  dw.getDocumentDOM().source;
    var selOffsets = domSource.getSelection();
    domSource.insert(selOffsets[1], html); // insert at the end of the selection in code view
    domSource.setSelection(selOffsets[1], selOffsets[1] + html.length); // Select the inserted code
    domSource.syncCodeToDOM();
}

function insertHTMLElement(html,isFluid) {
	if (dw.getFocus(false) === 'textView') 
	{
        insertHTMLAtIP(html);
        var insertedElm = document.getElementById("tagname");
        if ((!insertedElm)) {
            return;
        }
        insertedElm = insertedElm.value;
        if (insertedElm) {
            if (isFluid) {
                dw.logEvent(UT_FLUID_GRID_CODEVIEW, UT_FLUID_GRID_INSERT_DW + insertedElm + UT_FLUID_GRID_INSERT_INSERTED + UT_FLUID_GRID_INSERT_FLUID);
            } else {
                dw.logEvent(UT_FLUID_GRID_CODEVIEW, UT_FLUID_GRID_INSERT_DW + insertedElm + UT_FLUID_GRID_INSERT_INSERTED + UT_FLUID_GRID_INSERT_NOTFLUID);
            }
        }
	   return;
	}
	var dom = dw.getDocumentDOM();
	var details = getGridContainerDetailsForSelection();
	var selOption = insertOption;
	var tagNode = dom.getSelectedNode();
	if(isFluid&& !details.isSelectionInsideGridContainer && details.NearestGridConatiner)
	{
	    tagNode = details.NearestGridConatiner;
		selOption = 'nest';
	}
	else if(!isFluid && gridContainerDetailCache.bodySelected)
	{
		selOption = 'nest';
	}
	if (selOption === null || selOption === 'wrap')
	{
		var selection = dw.getSelection();
		if (selOption === null)
			dom.insertHTML(html, true, false); //insert in place
		else
		{
			if(tagNode !== null && tagNode.outerHTML === undefined )
			{
				//the tag node outer html will be undefined if the user has clicked inside the 
				//contents of a tag.[ie. there is no selection and the ip is inside the tag content]
				tagNode = tagNode.parentNode;
				var newSelection = dw.nodeToOffsets(tagNode);
				var startOffset = newSelection[0];
				var endOffset = newSelection[1];
				dw.setSelection(startOffset, endOffset);
			}
			dom.wrapTag(html, true, true); //wrap the current selection in the new element
		}
	}
	else
	{
		if (tagNode != null)
		{
			var newSelection = dw.nodeToOffsets(tagNode);
			var startOffset = newSelection[0];
			var endOffset = newSelection[1];
			if (selOption === 'before')
			{
				if(tagNode.outerHTML === undefined )
				{
				  //the tag node outer html will be undefined if the user has clicked inside the 
				  //contents of a tag.[ie. there is no selection and the ip is inside the tag content]
				  tagNode = tagNode.parentNode;
				  newSelection = dw.nodeToOffsets(tagNode);
				  startOffset = newSelection[0];
				  endOffset = newSelection[1];
				}
				endOffset = startOffset + html.length;
				tagNode.outerHTML = html + tagNode.outerHTML;
			}
			else if (selOption === 'after')
			{
				if(tagNode.outerHTML === undefined )
				  tagNode = tagNode.parentNode;
				tagNode.outerHTML = tagNode.outerHTML + html;
				if(tagNode.nextSibling)
				{
					newSelection = dw.nodeToOffsets(tagNode.nextSibling);
					startOffset = newSelection[0];
					endOffset = newSelection[1];
				}
			}
			else if (selOption === 'insideStart')
			{
				if(tagNode.outerHTML === undefined )
				  tagNode = tagNode.parentNode;
				tagNode.innerHTML = html + tagNode.innerHTML;
				if(tagNode.firstChild)
				{
					newSelection = dw.nodeToOffsets(tagNode.firstChild);
					startOffset = newSelection[0];
					endOffset = newSelection[1];
				}
			}
			else if (selOption === 'nest') // append as last child
			{
				if(tagNode.outerHTML === undefined )
				  tagNode = tagNode.parentNode;
				tagNode.innerHTML = tagNode.innerHTML + html;
				if(tagNode.lastChild)
				{
					newSelection = dw.nodeToOffsets(tagNode.lastChild);
					startOffset = newSelection[0];
					endOffset = newSelection[1];
				}
			}
			else
				return; // unknown insert option

			//now update the selection
			if ((startOffset < endOffset) &&
			(!dw.getDocumentDOM().rangeContainsLockedRegion(startOffset, endOffset)))
			{
				dw.setSelection(startOffset, endOffset);
			}
		}
	}
    var insertedElt = document.getElementById("tagname");
    if ((!insertedElt) || (tagNode.nodeType !== Node.ELEMENT_NODE) || (!selOption)) {
        return;
    }
    var position = selOption;
    var selectedElt = tagNode.tagName;
    insertedElt = insertedElt.value;
    if (insertedElt) {
        if (isFluid) {
            dw.logEvent(UT_FLUID_GRID_ELV_IP, UT_FLUID_GRID_INSERT_DW + insertedElt + UT_FLUID_GRID_INSERT_INSERTED + position + " " + selectedElt + UT_FLUID_GRID_INSERT_FLUID);
        } else {
            dw.logEvent(UT_FLUID_GRID_ELV_IP, UT_FLUID_GRID_INSERT_DW + insertedElt + UT_FLUID_GRID_INSERT_INSERTED + position + " " + selectedElt + UT_FLUID_GRID_INSERT_NOTFLUID);
        }
    }
}

function insertFluidElement(elementName, cssSelector, cssType, styleSheetManager) {		
    var newFluidElement = new CssGrids.FluidGridLayoutElement(
															elementName,
															dw,
															dwscripts,
															styleSheetManager
														    );
    newFluidElement.insert(cssSelector, cssType);
}
