var activeDoc = app.activeDocument;

doc_width = activeDoc.width;
doc_height = activeDoc.height;

var layers_list = new Array;

main();

function main() {
    CollectAllLayers(activeDoc)
    for (var i = 0; i < layers_list.length; i++){
        layer_width = layers_list[i].bounds[2] - layers_list[i].bounds[0];
        layer_height = layers_list[i].bounds[3] - layers_list[i].bounds[1];

        if (layer_width > doc_width * 1.5 || layer_height > doc_height * 1.5){
            activeDoc.crop([0,0,doc_width, doc_height])
        }
    }
    activeDoc.save()
    executeAction(app.charIDToTypeID('quit'), undefined, DialogModes.NO);
}

// Collect all layers in a document
function CollectAllLayers(obj){
    for ( var i = obj.layers.length-1; 0 <= i; i--){
        var layer = obj.layers[i];
        if (layer.typename === "ArtLayer"){
            layers_list.push(obj.layers[i]);
        }
        else {
            CollectAllLayers(obj.layers[i]);
        }
    }
    return layers_list;
}

