"""For the BLISS demo session.

* `blissoda.demo.processors`: Processor classes adapted for the Bliss demo session.
* `blissoda.demo.testing`: pytest-like helper functions to create integration tests.
  * See `blissoda.demo.scripts.template` on how they are intended.
* `blissoda.demo.scripts`: Bliss users scripts
  * To be loaded with `user_script_load` after `user_script_homedir_oda`.
  * Use `blissoda.demo.testing` to create integration tests.
"""

import os

EWOKS_EVENTS_DIR = os.path.join(
    os.path.abspath(os.environ.get("DEMO_TMP_ROOT", ".")), "ewoks_events"
)

EWOKS_RESULTS_DIR = os.path.join(
    os.path.abspath(os.environ.get("DEMO_TMP_ROOT", ".")), "ewoks_results"
)
