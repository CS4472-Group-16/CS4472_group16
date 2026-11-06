# Assignment 1 failure log

First full Java 11 test run: started 2026-11-06T01:12:35Z; Maven finished 2026-11-06T01:13:07Z (Nov 5, 8:13 p.m. Toronto).
Full run duration: 31.279 seconds, including remaining dependency downloads/build setup.
All failures below were exposed in this first run. Testing before each discovery was therefore at most 31.279 seconds.
Diagnosis shared one review window from the completed run to 2026-11-06T01:16:55+00:00. Individual per-fault diagnosis stopwatches were not recorded; do not add these shared durations together.
This is an automated-work record, not a claim about time spent by individual teammates. Append your own testing/diagnosis work for Assignment 3.

| Failure ID | First exposing case | Cases | Testing before discovery | Diagnosis record |
|---|---|---:|---|---|
| P-LENGTH | P01 | 26 | <=31.279 s, first full run | Shared window above; see localization table |
| S-POSITIVE | S36 | 2 | <=31.279 s, first full run | Shared window above; see localization table |
| S-BILLS | S42 | 3 | <=31.279 s, first full run | Shared window above; see localization table |
| S-LIMIT | S49 | 1 | <=31.279 s, first full run | Shared window above; see localization table |
| W-INVALID | W0001 | 588 | <=31.279 s, first full run | Shared window above; see localization table |
| W-STUDENT | W0452 | 385 | <=31.279 s, first full run | Shared window above; see localization table |
| W-LOW | W0461 | 105 | <=31.279 s, first full run | Shared window above; see localization table |
| W-HIGH | W0569 | 105 | <=31.279 s, first full run | Shared window above; see localization table |
| D-STUDENT-LOW | D01 | 4 | <=31.279 s, first full run | Shared window above; see localization table |
| D-STUDENT-HIGH | D04 | 3 | <=31.279 s, first full run | Shared window above; see localization table |
| D-NONSTUDENT-LOW | D07 | 5 | <=31.279 s, first full run | Shared window above; see localization table |
| D-NONSTUDENT-HIGH | D10 | 4 | <=31.279 s, first full run | Shared window above; see localization table |
| D-INVALID | D21 | 4 | <=31.279 s, first full run | Shared window above; see localization table |
| T-RULES | T01 | 16 | <=31.279 s, first full run | Shared window above; see localization table |

Every failed case, assertion message, runtime, and failure-group ID is preserved in [assignment1-results.csv](assignment1-results.csv).
Suspected statements and justifications are in [assignment1-localization.md](assignment1-localization.md).
The 592 invalid-fee-input failures are assumption-dependent; the other 659 are specification disagreements.

No production source changes were made. The daily-limit and console-interface mismatch remains for instructor clarification.
