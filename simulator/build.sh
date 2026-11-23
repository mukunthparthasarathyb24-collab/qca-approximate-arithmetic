#!/bin/sh
# Builds the headless QCADesigner-E runner (qca_run) from the official QCADesigner-E source.
# Needs: gcc, glib-2.0 dev headers (Ubuntu: sudo apt install build-essential libglib2.0-dev)
set -e
[ -d QCADesigner-E ] || git clone --depth 1 https://github.com/FSillT/QCADesigner-E.git
SRC=QCADesigner-E/QCADesignerE/src
cp qca_run.c $SRC/
cd $SRC
gcc -O2 -w -fcommon -DSTDIO_FILEIO -DPACKAGE_DATA_DIR=\"/usr/share\" -DPACKAGE_LOCALE_DIR=\"/usr/share/locale\" -I. \
  $(pkg-config --cflags glib-2.0 gobject-2.0) \
  fileio.c fileio_helpers.c custom_widgets.c simulation.c simulation_data.c bistable_simulation.c \
  coherence_vector.c coherence_vector_energy.c design.c objects/QCADCell.c objects/QCADCompoundDO.c \
  objects/QCADDesignObject.c objects/QCADDOContainer.c objects/QCADLabel.c objects/QCADLayer.c \
  objects/QCADRuler.c objects/QCADStretchyObject.c objects/QCADSubstrate.c exp_array.c \
  objects/object_helpers.c hsl2rgb.c generic_utils.c graph_dialog_widget_data.c vector_table.c qca_run.c \
  -o ../../../qca_run $(pkg-config --libs glib-2.0 gobject-2.0) -lm
echo "built ./qca_run"
