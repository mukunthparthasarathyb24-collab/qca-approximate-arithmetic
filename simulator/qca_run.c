/* qca_run: headless driver for QCADesigner-E simulation engines.
 * Usage: qca_run file.qca ENGINE options_file out.csv [vectors.txt]
 *   ENGINE = BISTABLE | COHERENCE_VECTOR_ENERGY
 *   vectors.txt (optional): first line = input labels separated by spaces,
 *   following lines = 0/1 values in that order. Without it: exhaustive.
 * Writes every input/output trace (polarisation per sample) and the clocks.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <glib.h>
#include <glib-object.h>
#include "global_consts.h"
#include "simulation_data.h"
#include "fileio.h"
#include "design.h"
#include "simulation.h"
#include "vector_table.h"
#include "bistable_simulation.h"
#include "coherence_vector.h"
#include "coherence_vector_energy.h"
#include "objects/QCADCell.h"
#include "objects/QCADLayer.h"
#include "objects/QCADLabel.h"
#include "objects/QCADSubstrate.h"
#include "objects/QCADRuler.h"

extern bistable_OP bistable_options;
extern coherence_energy_OP coherence_energy_options;

static VectorTable *load_vectors(const char *fname, DESIGN *design)
  {
  FILE *f = fopen(fname, "r");
  char line[4096], *tok;
  char *names[64]; int nnames = 0, map[64], Nix, Nix1, nin, row = 0;
  VectorTable *pvt;
  if (!f) { fprintf(stderr, "cannot open %s\n", fname); exit(4); }
  pvt = VectorTable_new();
  VectorTable_fill(pvt, design);
  nin = pvt->inputs->icUsed;
  if (!fgets(line, sizeof line, f)) exit(4);
  for (tok = strtok(line, " \t\r\n,"); tok; tok = strtok(NULL, " \t\r\n,"))
    names[nnames++] = g_strdup(tok);
  for (Nix = 0; Nix < nnames; Nix++)
    {
    map[Nix] = -1;
    for (Nix1 = 0; Nix1 < nin; Nix1++)
      if (!strcmp(names[Nix], qcad_cell_get_label(exp_array_index_1d(pvt->inputs, VT_INPUT, Nix1).input)))
        map[Nix] = Nix1;
    if (map[Nix] < 0) { fprintf(stderr, "input %s not in design\n", names[Nix]); exit(5); }
    }
  while (fgets(line, sizeof line, f))
    {
    int col = 0;
    if (strlen(line) < 2) continue;
    VectorTable_add_vector(pvt, row);
    for (tok = strtok(line, " \t\r\n,"); tok && col < nnames; tok = strtok(NULL, " \t\r\n,"), col++)
      exp_array_index_2d(pvt->vectors, gboolean, row, map[col]) = (atoi(tok) != 0);
    row++;
    }
  fclose(f);
  fprintf(stderr, "Loaded %d vectors for %d inputs\n", row, nin);
  return pvt;
  }

int main(int argc, char **argv)
  {
  DESIGN *design = NULL;
  simulation_data *sd;
  VectorTable *pvt = NULL;
  int engine, sim_type = EXHAUSTIVE_VERIFICATION, i, j, ntr;
  FILE *out;

  if (argc < 5) { fprintf(stderr, "usage: qca_run file.qca ENGINE opts out.csv [vectors]\n"); return 1; }
#if !GLIB_CHECK_VERSION(2,36,0)
  g_type_init();
#endif
  g_type_class_ref(QCAD_TYPE_CELL); g_type_class_ref(QCAD_TYPE_LAYER); g_type_class_ref(QCAD_TYPE_LABEL);
  g_type_class_ref(QCAD_TYPE_SUBSTRATE); g_type_class_ref(QCAD_TYPE_RULER);
  if (!open_project_file(argv[1], &design) || !design) { fprintf(stderr, "bad qca file\n"); return 3; }
  fprintf(stderr, "design: %d inputs, %d outputs\n", design->bus_layout->inputs->icUsed, design->bus_layout->outputs->icUsed);

  if (!strcmp(argv[2], "BISTABLE"))
    {
    bistable_OP *bo = open_bistable_options_file(argv[3]);
    if (!bo) return 2;
    memcpy(&bistable_options, bo, sizeof *bo);
    engine = BISTABLE;
    }
  else
    {
    /* argv[3]: comma list key=value applied on top of QCADesigner-E defaults */
    char *spec = g_strdup(argv[3]), *kv;
    for (kv = strtok(spec, ","); kv; kv = strtok(NULL, ","))
      {
      char *eq = strchr(kv, '='); double v;
      if (!eq) continue; *eq = 0; v = g_ascii_strtod(eq + 1, NULL);
      if (!strcmp(kv, "T")) coherence_energy_options.T = v;
      else if (!strcmp(kv, "duration")) coherence_energy_options.duration = v;
      else if (!strcmp(kv, "clock_period")) coherence_energy_options.clock_period = v;
      else if (!strcmp(kv, "input_period")) coherence_energy_options.input_period = v;
      else if (!strcmp(kv, "time_step")) coherence_energy_options.time_step = v;
      else if (!strcmp(kv, "relaxation")) coherence_energy_options.relaxation = v;
      else if (!strcmp(kv, "radius_of_effect")) coherence_energy_options.radius_of_effect = v;
      else if (!strcmp(kv, "zero_mode")) coherence_energy_options.zero_mode_act = (v != 0);
      else if (!strcmp(kv, "clock_type")) coherence_energy_options.clock_type = (int)v;
      else fprintf(stderr, "unknown key %s\n", kv);
      }
    coherence_energy_options_dump(&coherence_energy_options, stderr);
    engine = COHERENCE_VECTOR_ENERGY;
    }
  if (argc > 5) { pvt = load_vectors(argv[5], design); sim_type = VECTOR_TABLE; }
  else pvt = VectorTable_new();

  sd = run_simulation(engine, sim_type, design, pvt);
  if (!sd) { fprintf(stderr, "simulation failed\n"); return 6; }

  out = fopen(argv[4], "w");
  ntr = design->bus_layout->inputs->icUsed + design->bus_layout->outputs->icUsed;
  fprintf(out, "sample");
  for (i = 0; i < ntr; i++) fprintf(out, ",%s%s", sd->trace[i].trace_function == QCAD_CELL_INPUT ? "in:" : "out:", sd->trace[i].data_labels);
  for (i = 0; i < 4; i++) fprintf(out, ",clk%d", i);
  fprintf(out, "\n");
  for (j = 0; j < sd->number_samples; j++)
    {
    fprintf(out, "%d", j);
    for (i = 0; i < ntr; i++) fprintf(out, ",%.4f", sd->trace[i].data[j]);
    for (i = 0; i < 4; i++) fprintf(out, ",%.4e", sd->clock_data[i].data[j]);
    fprintf(out, "\n");
    }
  fclose(out);
  fprintf(stderr, "wrote %d samples x %d traces\n", sd->number_samples, ntr);
  return 0;
  }
