# Assignment 1: black-box testing

## 1. Process, traceability, and assumptions

The oracle is the supplied Assignment 1 business specification. The fixed CSV
fixtures under `src/test/resources/assignment1` contain the expected results;
JUnit does not calculate its expectations by calling the implementation.
`tools/generate_assignment1_cases.py` records how the specification produced
those fixtures. Monetary comparisons use an absolute tolerance of $0.000000001;
fees are not rounded to cents because the specification gives no rounding rule.
Leading zeros in PINs are retained. Cases use fresh objects/accounts and do not
depend on the current day or a real database. Calendar days use Java's public
convention: Sunday=1, Monday=2, ..., Saturday=7.

### Session: robust boundary analysis with the single-fault instruction

The assignment says both "robust worst case" and "single fault assumption."
An unrestricted Cartesian product of invalid PINs and invalid amounts would
violate the latter. We therefore cross the **valid** PIN boundary values with
the amount boundary values, and test each invalid PIN separately while other
inputs are nominal. Invalid lexical PIN cases vary one character at a time.
This explicitly favors the single-fault instruction when the two conflict.

A PIN is a string of exactly five ASCII digits, not an integer credential.
Its numeric boundary representatives are `00000`, `00001`, `50000`, `99998`,
`99999`; robust outside probes are `-0001` and `100000`. Length probes include
4, 5, and 6 characters, plus empty/one-character strings. Supplemental lexical
probes exercise `/`, `0`, `1`, `8`, `9`, `:` at every character position, using
`55555` elsewhere, along with a letter and a space.

Withdrawal amounts are integer dollars. The operational range is $20 through
$1,000: $20 is the smallest positive dispensable amount and $1,000 is the
specified daily limit. Boundary values are 19, 20, 21, 500, 999, 1000, 1001;
each is paired with each of the five valid PIN representatives (35 cases).
Only 20, 500, 1000 of those amounts are dispensable. Supplemental cases cover
negative/zero values, 30 (an interior denomination gap), 40, 50, 60, 70, 80, 90,
110, 990 (nearest valid amount below the limit), and 1010/1020. In particular,
1020 isolates the upper-limit fault from denomination validation. A positive
amount is dispensable iff there exist nonnegative integers x,y with
`amount = 20*x + 50*y`; the oracle enumerates possible counts of $50 bills.

**Repository/specification mismatch:** this starter has a Swing UI and no console
entry point, no daily-limit account field, and no API to configure that limit.
The tests use the public withdrawal transaction type corresponding to console
choice 1; they cannot test console parsing. Each amount test creates a fresh
Mockito account with available balance $5,000 and uses $1,000 as the required
oracle limit. This does **not** claim to configure a nonexistent production
daily-limit field. Tests reveal the missing enforcement instead of implementing
it in a mock. Cumulative withdrawals within a day are outside these fresh-account
boundary cases and remain a limitation until the missing facility is clarified.

PIN validation is exposed by `ATM.checkPin`, which delegates valid input to the
Session; `Session.addPin` itself does not validate format. PIN tests therefore
enter through the real ATM facade and real FormatChecker, mocking only external
credentials/UI. Amount tests enter Session directly to prevent the known PIN
fault from masking amount validation. They execute the real session states,
ATMWithdrawal, JavaDispatcher, BankFacade, and BankWithdrawal, with an account
double and a zero-fee calculator double. Fee behavior is independently tested in
the three calculator suites. No target method or cash validator is mocked.

### Withdrawal fees: robust worst-case boundary analysis

Monetary resolution is one cent. Amount representatives are
`{-0.01, 0, 0.01, 500, 999.99, 1000, 1000.01}`. Balance representatives are
`{-0.01, 0, 0.01, 999.99, 1000, 1000.01, 4999.99, 5000, 5000.01,
9999.99, 10000, 10000.01}`. Include both student values and all day codes 0..8,
including the robust invalid codes just outside 1..7. The complete Cartesian
product contains **7 x 12 x 2 x 9 = 1,512 cases**. Unlike Session, this target
does not have a single-fault restriction, so combinations of invalid values
are retained.

The real decision boundaries are $1,000/$5,000 balances and weekday/weekend.
The calculator specification gives no maximum amount or balance. $1,000 and
$10,000 are finite sampling-envelope edges, not assumed API rejection limits;
their just-above probes remain valid. Other than these chosen envelope probes,
the unbounded positive domain cannot have a finite upper boundary.

For students, the specified rate is 0 on weekdays and 0.001 on weekends.
For nonstudents it is 0.003 below $1,000, 0.001 from $1,000 inclusive through
less than $5,000, and 0 from $5,000 inclusive. Expected fee = amount x rate.

**Unspecified invalid-input contract:** negative monetary arguments and invalid
day codes are assumed to require `IllegalArgumentException`. The assignment does
not mandate this exception for FeesCalculator. These robust probes are marked
`REJECT` and localized separately as **assumption-dependent findings**, not
confirmed business-rule faults. Zero amount/balance is allowed for pure fee
calculation, independent of whether an ATM can dispense a zero-dollar withdrawal.
NaN/infinities, nulls, and fractional cents are outside the finite monetary model.

### Deposit fees: weak robust equivalence class analysis

For students the amount classes are `[0,50]`, `(50,infinity)`; balance classes
are `[0,500]`, `(500,5000]`, `(5000,infinity)`. Representatives are 25/75 and
250/1000/6000. For nonstudents the amount classes are `[0,250]`,
`(250,infinity)`; balances are `[0,2500]`, `(2500,10000]`, `(10000,infinity)`.
Representatives are 125/375 and 1000/5000/15000. The first twelve cases cover all
these valid classes (with extra valid combinations beyond the weak minimum).
Six equal-threshold cases document inclusivity, and two zero cases supplement
the design. The four invalid cases vary only negative amount or negative balance,
with the other dimensions nominal; combinations of invalid dimensions are not
generated. Total: **24 cases**. Negative-input rejection has the same explicit
assumption as withdrawal and is reported separately.

| Client | Amount class | Balance class | Specified fractional rate |
|---|---|---|---:|
| Student | >50 | >500 | 0.005 |
| Student | >50 | <=500 | 0.0025 |
| Student | <=50 | >5000 | 0.005 |
| Student | <=50 | <=5000 | 0 |
| Nonstudent | >250 | >2500 | 0.008 |
| Nonstudent | >250 | <=2500 | 0.004 |
| Nonstudent | <=250 | >10000 | 0 |
| Nonstudent | <=250 | <=10000 | 0.001 |

The repository calls this method `calculateDepositInterest`; we test its returned
value against the assignment's deposit-fee specification without changing its name.

### Transfer fees: decision table analysis

Four binary choices produce **16 feasible rules**: student status, amount class,
source balance class, destination balance class. No rules are impossible or
redundant because every leaf has a specified fee action. Thresholds depend on the
earlier choices; use the following table, not one global source/destination split.
For each balance, the low representative is threshold minus $1 and the high
representative equals the threshold. Amounts are 199/200 for students and 99/100
for nonstudents. Values at equality belong to the high branch. Each transfer is
less than its source balance. The complete executable decision table (including
the fractional rate and expected fee) is T01–T16 in section 2.

| Client | Amount | Source split | Destination split | Rates: low/low, low/high, high/low, high/high |
|---|---|---:|---:|---|
| Student | <200 | 2000 | 1000 | 0.001, 0.0005, 0.0005, 0.00025 |
| Student | >=200 | 2000 | 1000 | 0.0005, 0.00025, 0.0025, 0.00125 |
| Nonstudent | <100 | 4000 | 2000 | 0.002, 0.001, 0.01, 0.005 |
| Nonstudent | >=100 | 2000 | 1000 | 0.002, 0.001, 0.005, 0.0025 |

### Reproducing the evidence

Use Java 11 and Maven. Run `mvn -B checkstyle:check`, then
`mvn -B -Dmaven.test.failure.ignore=true test`. The latter tolerates assertion
failures but must still compile and execute all tests. Run
`python3 tools/record_assignment1_results.py` to refresh the tables from actual
Surefire XML, and `python3 tools/ci_report.py` for the coverage summary.
`mvn -B test` deliberately returns failure while the localized faults remain.
The original three example tests are retained and reported separately; the ATM
examples accept four-digit PINs and are legacy behavior tests, not the five-digit
specification oracle. The test phase does not repair production faults.

CI keeps lint mandatory, tolerates assertion failures on dev and `phase:tests`,
and requires a passing complete suite for `phase:fix`. Missing/ambiguous phase
labels fail the tests job. JUnit and coverage comments/artifacts are informational.
Maven compiler/Surefire versions are pinned so Java 11 compilation and JUnit 5
discovery do not depend on Maven's historical defaults; zero discovered tests fail.
Sources: [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
and [Maven Surefire JUnit Platform](https://maven.apache.org/components/surefire/maven-surefire-plugin/examples/junit-platform.html).

GenAI assisted test design, implementation, execution, and documentation. Team
members must review the assumptions, explain the techniques, and independently
check the results before submitting.

<!-- GENERATED RESULTS: tools/record_assignment1_results.py -->

## 2. Test-case tables and observed results

Generated from real Java 11 Surefire XML at 2026-11-06T01:18:11+00:00. All 1646 assignment cases executed.
**395 passed, 1251 failed, 0 errors, 0 skipped.**
Of the failures, 592 depend on the explicit invalid-input assumption; 659 expose specified behavior disagreements.

The three unchanged starter example tests also passed, bringing the full suite to 1,649 tests.

`REJECT` means assumed IllegalArgumentException for fee APIs. Session valid=false means the specified
InvalidPinFormatException or InvalidAmountException. A fault ID links each failure to section 3.

### Pin

| id | pin | valid | Observed | Fault |
|---|---|---|---|---|
| P01 | 00000 | true | FAIL | P-LENGTH |
| P02 | 00001 | true | FAIL | P-LENGTH |
| P03 | 50000 | true | FAIL | P-LENGTH |
| P04 | 99998 | true | FAIL | P-LENGTH |
| P05 | 99999 | true | FAIL | P-LENGTH |
| P06 | -0001 | false | PASS | — |
| P07 | 100000 | false | PASS | — |
| P08 | 1234 | false | FAIL | P-LENGTH |
| P09 | 123456 | false | PASS | — |
| P10 | 1 | false | PASS | — |
| P11 |  | false | PASS | — |
| P12 | 12a45 | false | PASS | — |
| P13 | 12/45 | false | PASS | — |
| P14 | 12:45 | false | PASS | — |
| P15 | 12 45 | false | PASS | — |
| P16 | /5555 | false | PASS | — |
| P17 | 05555 | true | FAIL | P-LENGTH |
| P18 | 15555 | true | FAIL | P-LENGTH |
| P19 | 85555 | true | FAIL | P-LENGTH |
| P20 | 95555 | true | FAIL | P-LENGTH |
| P21 | :5555 | false | PASS | — |
| P22 | 5/555 | false | PASS | — |
| P23 | 50555 | true | FAIL | P-LENGTH |
| P24 | 51555 | true | FAIL | P-LENGTH |
| P25 | 58555 | true | FAIL | P-LENGTH |
| P26 | 59555 | true | FAIL | P-LENGTH |
| P27 | 5:555 | false | PASS | — |
| P28 | 55/55 | false | PASS | — |
| P29 | 55055 | true | FAIL | P-LENGTH |
| P30 | 55155 | true | FAIL | P-LENGTH |
| P31 | 55855 | true | FAIL | P-LENGTH |
| P32 | 55955 | true | FAIL | P-LENGTH |
| P33 | 55:55 | false | PASS | — |
| P34 | 555/5 | false | PASS | — |
| P35 | 55505 | true | FAIL | P-LENGTH |
| P36 | 55515 | true | FAIL | P-LENGTH |
| P37 | 55585 | true | FAIL | P-LENGTH |
| P38 | 55595 | true | FAIL | P-LENGTH |
| P39 | 555:5 | false | PASS | — |
| P40 | 5555/ | false | PASS | — |
| P41 | 55550 | true | FAIL | P-LENGTH |
| P42 | 55551 | true | FAIL | P-LENGTH |
| P43 | 55558 | true | FAIL | P-LENGTH |
| P44 | 55559 | true | FAIL | P-LENGTH |
| P45 | 5555: | false | PASS | — |

### Session

| id | pin | amount | valid | Observed | Fault |
|---|---|---|---|---|---|
| S01 | 00000 | 19 | false | PASS | — |
| S02 | 00000 | 20 | true | PASS | — |
| S03 | 00000 | 21 | false | PASS | — |
| S04 | 00000 | 500 | true | PASS | — |
| S05 | 00000 | 999 | false | PASS | — |
| S06 | 00000 | 1000 | true | PASS | — |
| S07 | 00000 | 1001 | false | PASS | — |
| S08 | 00001 | 19 | false | PASS | — |
| S09 | 00001 | 20 | true | PASS | — |
| S10 | 00001 | 21 | false | PASS | — |
| S11 | 00001 | 500 | true | PASS | — |
| S12 | 00001 | 999 | false | PASS | — |
| S13 | 00001 | 1000 | true | PASS | — |
| S14 | 00001 | 1001 | false | PASS | — |
| S15 | 50000 | 19 | false | PASS | — |
| S16 | 50000 | 20 | true | PASS | — |
| S17 | 50000 | 21 | false | PASS | — |
| S18 | 50000 | 500 | true | PASS | — |
| S19 | 50000 | 999 | false | PASS | — |
| S20 | 50000 | 1000 | true | PASS | — |
| S21 | 50000 | 1001 | false | PASS | — |
| S22 | 99998 | 19 | false | PASS | — |
| S23 | 99998 | 20 | true | PASS | — |
| S24 | 99998 | 21 | false | PASS | — |
| S25 | 99998 | 500 | true | PASS | — |
| S26 | 99998 | 999 | false | PASS | — |
| S27 | 99998 | 1000 | true | PASS | — |
| S28 | 99998 | 1001 | false | PASS | — |
| S29 | 99999 | 19 | false | PASS | — |
| S30 | 99999 | 20 | true | PASS | — |
| S31 | 99999 | 21 | false | PASS | — |
| S32 | 99999 | 500 | true | PASS | — |
| S33 | 99999 | 999 | false | PASS | — |
| S34 | 99999 | 1000 | true | PASS | — |
| S35 | 99999 | 1001 | false | PASS | — |
| S36 | 50000 | -50 | false | FAIL | S-POSITIVE |
| S37 | 50000 | -1 | false | PASS | — |
| S38 | 50000 | 0 | false | FAIL | S-POSITIVE |
| S39 | 50000 | 30 | false | PASS | — |
| S40 | 50000 | 40 | true | PASS | — |
| S41 | 50000 | 50 | true | PASS | — |
| S42 | 50000 | 60 | true | FAIL | S-BILLS |
| S43 | 50000 | 70 | true | PASS | — |
| S44 | 50000 | 80 | true | FAIL | S-BILLS |
| S45 | 50000 | 90 | true | PASS | — |
| S46 | 50000 | 110 | true | FAIL | S-BILLS |
| S47 | 50000 | 990 | true | PASS | — |
| S48 | 50000 | 1010 | false | PASS | — |
| S49 | 50000 | 1020 | false | FAIL | S-LIMIT |

### Withdrawal

| id | amount | balance | student | day | expected | Observed | Fault |
|---|---|---|---|---|---|---|---|
| W0001 | -0.01 | -0.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0002 | -0.01 | -0.01 | true | 1 | REJECT | FAIL | W-INVALID |
| W0003 | -0.01 | -0.01 | true | 2 | REJECT | FAIL | W-INVALID |
| W0004 | -0.01 | -0.01 | true | 3 | REJECT | FAIL | W-INVALID |
| W0005 | -0.01 | -0.01 | true | 4 | REJECT | FAIL | W-INVALID |
| W0006 | -0.01 | -0.01 | true | 5 | REJECT | FAIL | W-INVALID |
| W0007 | -0.01 | -0.01 | true | 6 | REJECT | FAIL | W-INVALID |
| W0008 | -0.01 | -0.01 | true | 7 | REJECT | FAIL | W-INVALID |
| W0009 | -0.01 | -0.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0010 | -0.01 | -0.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0011 | -0.01 | -0.01 | false | 1 | REJECT | FAIL | W-INVALID |
| W0012 | -0.01 | -0.01 | false | 2 | REJECT | FAIL | W-INVALID |
| W0013 | -0.01 | -0.01 | false | 3 | REJECT | FAIL | W-INVALID |
| W0014 | -0.01 | -0.01 | false | 4 | REJECT | FAIL | W-INVALID |
| W0015 | -0.01 | -0.01 | false | 5 | REJECT | FAIL | W-INVALID |
| W0016 | -0.01 | -0.01 | false | 6 | REJECT | FAIL | W-INVALID |
| W0017 | -0.01 | -0.01 | false | 7 | REJECT | FAIL | W-INVALID |
| W0018 | -0.01 | -0.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0019 | -0.01 | 0 | true | 0 | REJECT | FAIL | W-INVALID |
| W0020 | -0.01 | 0 | true | 1 | REJECT | FAIL | W-INVALID |
| W0021 | -0.01 | 0 | true | 2 | REJECT | FAIL | W-INVALID |
| W0022 | -0.01 | 0 | true | 3 | REJECT | FAIL | W-INVALID |
| W0023 | -0.01 | 0 | true | 4 | REJECT | FAIL | W-INVALID |
| W0024 | -0.01 | 0 | true | 5 | REJECT | FAIL | W-INVALID |
| W0025 | -0.01 | 0 | true | 6 | REJECT | FAIL | W-INVALID |
| W0026 | -0.01 | 0 | true | 7 | REJECT | FAIL | W-INVALID |
| W0027 | -0.01 | 0 | true | 8 | REJECT | FAIL | W-INVALID |
| W0028 | -0.01 | 0 | false | 0 | REJECT | FAIL | W-INVALID |
| W0029 | -0.01 | 0 | false | 1 | REJECT | FAIL | W-INVALID |
| W0030 | -0.01 | 0 | false | 2 | REJECT | FAIL | W-INVALID |
| W0031 | -0.01 | 0 | false | 3 | REJECT | FAIL | W-INVALID |
| W0032 | -0.01 | 0 | false | 4 | REJECT | FAIL | W-INVALID |
| W0033 | -0.01 | 0 | false | 5 | REJECT | FAIL | W-INVALID |
| W0034 | -0.01 | 0 | false | 6 | REJECT | FAIL | W-INVALID |
| W0035 | -0.01 | 0 | false | 7 | REJECT | FAIL | W-INVALID |
| W0036 | -0.01 | 0 | false | 8 | REJECT | FAIL | W-INVALID |
| W0037 | -0.01 | 0.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0038 | -0.01 | 0.01 | true | 1 | REJECT | FAIL | W-INVALID |
| W0039 | -0.01 | 0.01 | true | 2 | REJECT | FAIL | W-INVALID |
| W0040 | -0.01 | 0.01 | true | 3 | REJECT | FAIL | W-INVALID |
| W0041 | -0.01 | 0.01 | true | 4 | REJECT | FAIL | W-INVALID |
| W0042 | -0.01 | 0.01 | true | 5 | REJECT | FAIL | W-INVALID |
| W0043 | -0.01 | 0.01 | true | 6 | REJECT | FAIL | W-INVALID |
| W0044 | -0.01 | 0.01 | true | 7 | REJECT | FAIL | W-INVALID |
| W0045 | -0.01 | 0.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0046 | -0.01 | 0.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0047 | -0.01 | 0.01 | false | 1 | REJECT | FAIL | W-INVALID |
| W0048 | -0.01 | 0.01 | false | 2 | REJECT | FAIL | W-INVALID |
| W0049 | -0.01 | 0.01 | false | 3 | REJECT | FAIL | W-INVALID |
| W0050 | -0.01 | 0.01 | false | 4 | REJECT | FAIL | W-INVALID |
| W0051 | -0.01 | 0.01 | false | 5 | REJECT | FAIL | W-INVALID |
| W0052 | -0.01 | 0.01 | false | 6 | REJECT | FAIL | W-INVALID |
| W0053 | -0.01 | 0.01 | false | 7 | REJECT | FAIL | W-INVALID |
| W0054 | -0.01 | 0.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0055 | -0.01 | 999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W0056 | -0.01 | 999.99 | true | 1 | REJECT | FAIL | W-INVALID |
| W0057 | -0.01 | 999.99 | true | 2 | REJECT | FAIL | W-INVALID |
| W0058 | -0.01 | 999.99 | true | 3 | REJECT | FAIL | W-INVALID |
| W0059 | -0.01 | 999.99 | true | 4 | REJECT | FAIL | W-INVALID |
| W0060 | -0.01 | 999.99 | true | 5 | REJECT | FAIL | W-INVALID |
| W0061 | -0.01 | 999.99 | true | 6 | REJECT | FAIL | W-INVALID |
| W0062 | -0.01 | 999.99 | true | 7 | REJECT | FAIL | W-INVALID |
| W0063 | -0.01 | 999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W0064 | -0.01 | 999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W0065 | -0.01 | 999.99 | false | 1 | REJECT | FAIL | W-INVALID |
| W0066 | -0.01 | 999.99 | false | 2 | REJECT | FAIL | W-INVALID |
| W0067 | -0.01 | 999.99 | false | 3 | REJECT | FAIL | W-INVALID |
| W0068 | -0.01 | 999.99 | false | 4 | REJECT | FAIL | W-INVALID |
| W0069 | -0.01 | 999.99 | false | 5 | REJECT | FAIL | W-INVALID |
| W0070 | -0.01 | 999.99 | false | 6 | REJECT | FAIL | W-INVALID |
| W0071 | -0.01 | 999.99 | false | 7 | REJECT | FAIL | W-INVALID |
| W0072 | -0.01 | 999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W0073 | -0.01 | 1000 | true | 0 | REJECT | FAIL | W-INVALID |
| W0074 | -0.01 | 1000 | true | 1 | REJECT | FAIL | W-INVALID |
| W0075 | -0.01 | 1000 | true | 2 | REJECT | FAIL | W-INVALID |
| W0076 | -0.01 | 1000 | true | 3 | REJECT | FAIL | W-INVALID |
| W0077 | -0.01 | 1000 | true | 4 | REJECT | FAIL | W-INVALID |
| W0078 | -0.01 | 1000 | true | 5 | REJECT | FAIL | W-INVALID |
| W0079 | -0.01 | 1000 | true | 6 | REJECT | FAIL | W-INVALID |
| W0080 | -0.01 | 1000 | true | 7 | REJECT | FAIL | W-INVALID |
| W0081 | -0.01 | 1000 | true | 8 | REJECT | FAIL | W-INVALID |
| W0082 | -0.01 | 1000 | false | 0 | REJECT | FAIL | W-INVALID |
| W0083 | -0.01 | 1000 | false | 1 | REJECT | FAIL | W-INVALID |
| W0084 | -0.01 | 1000 | false | 2 | REJECT | FAIL | W-INVALID |
| W0085 | -0.01 | 1000 | false | 3 | REJECT | FAIL | W-INVALID |
| W0086 | -0.01 | 1000 | false | 4 | REJECT | FAIL | W-INVALID |
| W0087 | -0.01 | 1000 | false | 5 | REJECT | FAIL | W-INVALID |
| W0088 | -0.01 | 1000 | false | 6 | REJECT | FAIL | W-INVALID |
| W0089 | -0.01 | 1000 | false | 7 | REJECT | FAIL | W-INVALID |
| W0090 | -0.01 | 1000 | false | 8 | REJECT | FAIL | W-INVALID |
| W0091 | -0.01 | 1000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0092 | -0.01 | 1000.01 | true | 1 | REJECT | FAIL | W-INVALID |
| W0093 | -0.01 | 1000.01 | true | 2 | REJECT | FAIL | W-INVALID |
| W0094 | -0.01 | 1000.01 | true | 3 | REJECT | FAIL | W-INVALID |
| W0095 | -0.01 | 1000.01 | true | 4 | REJECT | FAIL | W-INVALID |
| W0096 | -0.01 | 1000.01 | true | 5 | REJECT | FAIL | W-INVALID |
| W0097 | -0.01 | 1000.01 | true | 6 | REJECT | FAIL | W-INVALID |
| W0098 | -0.01 | 1000.01 | true | 7 | REJECT | FAIL | W-INVALID |
| W0099 | -0.01 | 1000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0100 | -0.01 | 1000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0101 | -0.01 | 1000.01 | false | 1 | REJECT | FAIL | W-INVALID |
| W0102 | -0.01 | 1000.01 | false | 2 | REJECT | FAIL | W-INVALID |
| W0103 | -0.01 | 1000.01 | false | 3 | REJECT | FAIL | W-INVALID |
| W0104 | -0.01 | 1000.01 | false | 4 | REJECT | FAIL | W-INVALID |
| W0105 | -0.01 | 1000.01 | false | 5 | REJECT | FAIL | W-INVALID |
| W0106 | -0.01 | 1000.01 | false | 6 | REJECT | FAIL | W-INVALID |
| W0107 | -0.01 | 1000.01 | false | 7 | REJECT | FAIL | W-INVALID |
| W0108 | -0.01 | 1000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0109 | -0.01 | 4999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W0110 | -0.01 | 4999.99 | true | 1 | REJECT | FAIL | W-INVALID |
| W0111 | -0.01 | 4999.99 | true | 2 | REJECT | FAIL | W-INVALID |
| W0112 | -0.01 | 4999.99 | true | 3 | REJECT | FAIL | W-INVALID |
| W0113 | -0.01 | 4999.99 | true | 4 | REJECT | FAIL | W-INVALID |
| W0114 | -0.01 | 4999.99 | true | 5 | REJECT | FAIL | W-INVALID |
| W0115 | -0.01 | 4999.99 | true | 6 | REJECT | FAIL | W-INVALID |
| W0116 | -0.01 | 4999.99 | true | 7 | REJECT | FAIL | W-INVALID |
| W0117 | -0.01 | 4999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W0118 | -0.01 | 4999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W0119 | -0.01 | 4999.99 | false | 1 | REJECT | FAIL | W-INVALID |
| W0120 | -0.01 | 4999.99 | false | 2 | REJECT | FAIL | W-INVALID |
| W0121 | -0.01 | 4999.99 | false | 3 | REJECT | FAIL | W-INVALID |
| W0122 | -0.01 | 4999.99 | false | 4 | REJECT | FAIL | W-INVALID |
| W0123 | -0.01 | 4999.99 | false | 5 | REJECT | FAIL | W-INVALID |
| W0124 | -0.01 | 4999.99 | false | 6 | REJECT | FAIL | W-INVALID |
| W0125 | -0.01 | 4999.99 | false | 7 | REJECT | FAIL | W-INVALID |
| W0126 | -0.01 | 4999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W0127 | -0.01 | 5000 | true | 0 | REJECT | FAIL | W-INVALID |
| W0128 | -0.01 | 5000 | true | 1 | REJECT | FAIL | W-INVALID |
| W0129 | -0.01 | 5000 | true | 2 | REJECT | FAIL | W-INVALID |
| W0130 | -0.01 | 5000 | true | 3 | REJECT | FAIL | W-INVALID |
| W0131 | -0.01 | 5000 | true | 4 | REJECT | FAIL | W-INVALID |
| W0132 | -0.01 | 5000 | true | 5 | REJECT | FAIL | W-INVALID |
| W0133 | -0.01 | 5000 | true | 6 | REJECT | FAIL | W-INVALID |
| W0134 | -0.01 | 5000 | true | 7 | REJECT | FAIL | W-INVALID |
| W0135 | -0.01 | 5000 | true | 8 | REJECT | FAIL | W-INVALID |
| W0136 | -0.01 | 5000 | false | 0 | REJECT | FAIL | W-INVALID |
| W0137 | -0.01 | 5000 | false | 1 | REJECT | FAIL | W-INVALID |
| W0138 | -0.01 | 5000 | false | 2 | REJECT | FAIL | W-INVALID |
| W0139 | -0.01 | 5000 | false | 3 | REJECT | FAIL | W-INVALID |
| W0140 | -0.01 | 5000 | false | 4 | REJECT | FAIL | W-INVALID |
| W0141 | -0.01 | 5000 | false | 5 | REJECT | FAIL | W-INVALID |
| W0142 | -0.01 | 5000 | false | 6 | REJECT | FAIL | W-INVALID |
| W0143 | -0.01 | 5000 | false | 7 | REJECT | FAIL | W-INVALID |
| W0144 | -0.01 | 5000 | false | 8 | REJECT | FAIL | W-INVALID |
| W0145 | -0.01 | 5000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0146 | -0.01 | 5000.01 | true | 1 | REJECT | FAIL | W-INVALID |
| W0147 | -0.01 | 5000.01 | true | 2 | REJECT | FAIL | W-INVALID |
| W0148 | -0.01 | 5000.01 | true | 3 | REJECT | FAIL | W-INVALID |
| W0149 | -0.01 | 5000.01 | true | 4 | REJECT | FAIL | W-INVALID |
| W0150 | -0.01 | 5000.01 | true | 5 | REJECT | FAIL | W-INVALID |
| W0151 | -0.01 | 5000.01 | true | 6 | REJECT | FAIL | W-INVALID |
| W0152 | -0.01 | 5000.01 | true | 7 | REJECT | FAIL | W-INVALID |
| W0153 | -0.01 | 5000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0154 | -0.01 | 5000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0155 | -0.01 | 5000.01 | false | 1 | REJECT | FAIL | W-INVALID |
| W0156 | -0.01 | 5000.01 | false | 2 | REJECT | FAIL | W-INVALID |
| W0157 | -0.01 | 5000.01 | false | 3 | REJECT | FAIL | W-INVALID |
| W0158 | -0.01 | 5000.01 | false | 4 | REJECT | FAIL | W-INVALID |
| W0159 | -0.01 | 5000.01 | false | 5 | REJECT | FAIL | W-INVALID |
| W0160 | -0.01 | 5000.01 | false | 6 | REJECT | FAIL | W-INVALID |
| W0161 | -0.01 | 5000.01 | false | 7 | REJECT | FAIL | W-INVALID |
| W0162 | -0.01 | 5000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0163 | -0.01 | 9999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W0164 | -0.01 | 9999.99 | true | 1 | REJECT | FAIL | W-INVALID |
| W0165 | -0.01 | 9999.99 | true | 2 | REJECT | FAIL | W-INVALID |
| W0166 | -0.01 | 9999.99 | true | 3 | REJECT | FAIL | W-INVALID |
| W0167 | -0.01 | 9999.99 | true | 4 | REJECT | FAIL | W-INVALID |
| W0168 | -0.01 | 9999.99 | true | 5 | REJECT | FAIL | W-INVALID |
| W0169 | -0.01 | 9999.99 | true | 6 | REJECT | FAIL | W-INVALID |
| W0170 | -0.01 | 9999.99 | true | 7 | REJECT | FAIL | W-INVALID |
| W0171 | -0.01 | 9999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W0172 | -0.01 | 9999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W0173 | -0.01 | 9999.99 | false | 1 | REJECT | FAIL | W-INVALID |
| W0174 | -0.01 | 9999.99 | false | 2 | REJECT | FAIL | W-INVALID |
| W0175 | -0.01 | 9999.99 | false | 3 | REJECT | FAIL | W-INVALID |
| W0176 | -0.01 | 9999.99 | false | 4 | REJECT | FAIL | W-INVALID |
| W0177 | -0.01 | 9999.99 | false | 5 | REJECT | FAIL | W-INVALID |
| W0178 | -0.01 | 9999.99 | false | 6 | REJECT | FAIL | W-INVALID |
| W0179 | -0.01 | 9999.99 | false | 7 | REJECT | FAIL | W-INVALID |
| W0180 | -0.01 | 9999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W0181 | -0.01 | 10000 | true | 0 | REJECT | FAIL | W-INVALID |
| W0182 | -0.01 | 10000 | true | 1 | REJECT | FAIL | W-INVALID |
| W0183 | -0.01 | 10000 | true | 2 | REJECT | FAIL | W-INVALID |
| W0184 | -0.01 | 10000 | true | 3 | REJECT | FAIL | W-INVALID |
| W0185 | -0.01 | 10000 | true | 4 | REJECT | FAIL | W-INVALID |
| W0186 | -0.01 | 10000 | true | 5 | REJECT | FAIL | W-INVALID |
| W0187 | -0.01 | 10000 | true | 6 | REJECT | FAIL | W-INVALID |
| W0188 | -0.01 | 10000 | true | 7 | REJECT | FAIL | W-INVALID |
| W0189 | -0.01 | 10000 | true | 8 | REJECT | FAIL | W-INVALID |
| W0190 | -0.01 | 10000 | false | 0 | REJECT | FAIL | W-INVALID |
| W0191 | -0.01 | 10000 | false | 1 | REJECT | FAIL | W-INVALID |
| W0192 | -0.01 | 10000 | false | 2 | REJECT | FAIL | W-INVALID |
| W0193 | -0.01 | 10000 | false | 3 | REJECT | FAIL | W-INVALID |
| W0194 | -0.01 | 10000 | false | 4 | REJECT | FAIL | W-INVALID |
| W0195 | -0.01 | 10000 | false | 5 | REJECT | FAIL | W-INVALID |
| W0196 | -0.01 | 10000 | false | 6 | REJECT | FAIL | W-INVALID |
| W0197 | -0.01 | 10000 | false | 7 | REJECT | FAIL | W-INVALID |
| W0198 | -0.01 | 10000 | false | 8 | REJECT | FAIL | W-INVALID |
| W0199 | -0.01 | 10000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0200 | -0.01 | 10000.01 | true | 1 | REJECT | FAIL | W-INVALID |
| W0201 | -0.01 | 10000.01 | true | 2 | REJECT | FAIL | W-INVALID |
| W0202 | -0.01 | 10000.01 | true | 3 | REJECT | FAIL | W-INVALID |
| W0203 | -0.01 | 10000.01 | true | 4 | REJECT | FAIL | W-INVALID |
| W0204 | -0.01 | 10000.01 | true | 5 | REJECT | FAIL | W-INVALID |
| W0205 | -0.01 | 10000.01 | true | 6 | REJECT | FAIL | W-INVALID |
| W0206 | -0.01 | 10000.01 | true | 7 | REJECT | FAIL | W-INVALID |
| W0207 | -0.01 | 10000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0208 | -0.01 | 10000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0209 | -0.01 | 10000.01 | false | 1 | REJECT | FAIL | W-INVALID |
| W0210 | -0.01 | 10000.01 | false | 2 | REJECT | FAIL | W-INVALID |
| W0211 | -0.01 | 10000.01 | false | 3 | REJECT | FAIL | W-INVALID |
| W0212 | -0.01 | 10000.01 | false | 4 | REJECT | FAIL | W-INVALID |
| W0213 | -0.01 | 10000.01 | false | 5 | REJECT | FAIL | W-INVALID |
| W0214 | -0.01 | 10000.01 | false | 6 | REJECT | FAIL | W-INVALID |
| W0215 | -0.01 | 10000.01 | false | 7 | REJECT | FAIL | W-INVALID |
| W0216 | -0.01 | 10000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0217 | 0 | -0.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0218 | 0 | -0.01 | true | 1 | REJECT | FAIL | W-INVALID |
| W0219 | 0 | -0.01 | true | 2 | REJECT | FAIL | W-INVALID |
| W0220 | 0 | -0.01 | true | 3 | REJECT | FAIL | W-INVALID |
| W0221 | 0 | -0.01 | true | 4 | REJECT | FAIL | W-INVALID |
| W0222 | 0 | -0.01 | true | 5 | REJECT | FAIL | W-INVALID |
| W0223 | 0 | -0.01 | true | 6 | REJECT | FAIL | W-INVALID |
| W0224 | 0 | -0.01 | true | 7 | REJECT | FAIL | W-INVALID |
| W0225 | 0 | -0.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0226 | 0 | -0.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0227 | 0 | -0.01 | false | 1 | REJECT | FAIL | W-INVALID |
| W0228 | 0 | -0.01 | false | 2 | REJECT | FAIL | W-INVALID |
| W0229 | 0 | -0.01 | false | 3 | REJECT | FAIL | W-INVALID |
| W0230 | 0 | -0.01 | false | 4 | REJECT | FAIL | W-INVALID |
| W0231 | 0 | -0.01 | false | 5 | REJECT | FAIL | W-INVALID |
| W0232 | 0 | -0.01 | false | 6 | REJECT | FAIL | W-INVALID |
| W0233 | 0 | -0.01 | false | 7 | REJECT | FAIL | W-INVALID |
| W0234 | 0 | -0.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0235 | 0 | 0 | true | 0 | REJECT | FAIL | W-INVALID |
| W0236 | 0 | 0 | true | 1 | 0.000 | PASS | — |
| W0237 | 0 | 0 | true | 2 | 0 | PASS | — |
| W0238 | 0 | 0 | true | 3 | 0 | PASS | — |
| W0239 | 0 | 0 | true | 4 | 0 | PASS | — |
| W0240 | 0 | 0 | true | 5 | 0 | PASS | — |
| W0241 | 0 | 0 | true | 6 | 0 | PASS | — |
| W0242 | 0 | 0 | true | 7 | 0.000 | PASS | — |
| W0243 | 0 | 0 | true | 8 | REJECT | FAIL | W-INVALID |
| W0244 | 0 | 0 | false | 0 | REJECT | FAIL | W-INVALID |
| W0245 | 0 | 0 | false | 1 | 0.000 | PASS | — |
| W0246 | 0 | 0 | false | 2 | 0.000 | PASS | — |
| W0247 | 0 | 0 | false | 3 | 0.000 | PASS | — |
| W0248 | 0 | 0 | false | 4 | 0.000 | PASS | — |
| W0249 | 0 | 0 | false | 5 | 0.000 | PASS | — |
| W0250 | 0 | 0 | false | 6 | 0.000 | PASS | — |
| W0251 | 0 | 0 | false | 7 | 0.000 | PASS | — |
| W0252 | 0 | 0 | false | 8 | REJECT | FAIL | W-INVALID |
| W0253 | 0 | 0.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0254 | 0 | 0.01 | true | 1 | 0.000 | PASS | — |
| W0255 | 0 | 0.01 | true | 2 | 0 | PASS | — |
| W0256 | 0 | 0.01 | true | 3 | 0 | PASS | — |
| W0257 | 0 | 0.01 | true | 4 | 0 | PASS | — |
| W0258 | 0 | 0.01 | true | 5 | 0 | PASS | — |
| W0259 | 0 | 0.01 | true | 6 | 0 | PASS | — |
| W0260 | 0 | 0.01 | true | 7 | 0.000 | PASS | — |
| W0261 | 0 | 0.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0262 | 0 | 0.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0263 | 0 | 0.01 | false | 1 | 0.000 | PASS | — |
| W0264 | 0 | 0.01 | false | 2 | 0.000 | PASS | — |
| W0265 | 0 | 0.01 | false | 3 | 0.000 | PASS | — |
| W0266 | 0 | 0.01 | false | 4 | 0.000 | PASS | — |
| W0267 | 0 | 0.01 | false | 5 | 0.000 | PASS | — |
| W0268 | 0 | 0.01 | false | 6 | 0.000 | PASS | — |
| W0269 | 0 | 0.01 | false | 7 | 0.000 | PASS | — |
| W0270 | 0 | 0.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0271 | 0 | 999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W0272 | 0 | 999.99 | true | 1 | 0.000 | PASS | — |
| W0273 | 0 | 999.99 | true | 2 | 0 | PASS | — |
| W0274 | 0 | 999.99 | true | 3 | 0 | PASS | — |
| W0275 | 0 | 999.99 | true | 4 | 0 | PASS | — |
| W0276 | 0 | 999.99 | true | 5 | 0 | PASS | — |
| W0277 | 0 | 999.99 | true | 6 | 0 | PASS | — |
| W0278 | 0 | 999.99 | true | 7 | 0.000 | PASS | — |
| W0279 | 0 | 999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W0280 | 0 | 999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W0281 | 0 | 999.99 | false | 1 | 0.000 | PASS | — |
| W0282 | 0 | 999.99 | false | 2 | 0.000 | PASS | — |
| W0283 | 0 | 999.99 | false | 3 | 0.000 | PASS | — |
| W0284 | 0 | 999.99 | false | 4 | 0.000 | PASS | — |
| W0285 | 0 | 999.99 | false | 5 | 0.000 | PASS | — |
| W0286 | 0 | 999.99 | false | 6 | 0.000 | PASS | — |
| W0287 | 0 | 999.99 | false | 7 | 0.000 | PASS | — |
| W0288 | 0 | 999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W0289 | 0 | 1000 | true | 0 | REJECT | FAIL | W-INVALID |
| W0290 | 0 | 1000 | true | 1 | 0.000 | PASS | — |
| W0291 | 0 | 1000 | true | 2 | 0 | PASS | — |
| W0292 | 0 | 1000 | true | 3 | 0 | PASS | — |
| W0293 | 0 | 1000 | true | 4 | 0 | PASS | — |
| W0294 | 0 | 1000 | true | 5 | 0 | PASS | — |
| W0295 | 0 | 1000 | true | 6 | 0 | PASS | — |
| W0296 | 0 | 1000 | true | 7 | 0.000 | PASS | — |
| W0297 | 0 | 1000 | true | 8 | REJECT | FAIL | W-INVALID |
| W0298 | 0 | 1000 | false | 0 | REJECT | FAIL | W-INVALID |
| W0299 | 0 | 1000 | false | 1 | 0.000 | PASS | — |
| W0300 | 0 | 1000 | false | 2 | 0.000 | PASS | — |
| W0301 | 0 | 1000 | false | 3 | 0.000 | PASS | — |
| W0302 | 0 | 1000 | false | 4 | 0.000 | PASS | — |
| W0303 | 0 | 1000 | false | 5 | 0.000 | PASS | — |
| W0304 | 0 | 1000 | false | 6 | 0.000 | PASS | — |
| W0305 | 0 | 1000 | false | 7 | 0.000 | PASS | — |
| W0306 | 0 | 1000 | false | 8 | REJECT | FAIL | W-INVALID |
| W0307 | 0 | 1000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0308 | 0 | 1000.01 | true | 1 | 0.000 | PASS | — |
| W0309 | 0 | 1000.01 | true | 2 | 0 | PASS | — |
| W0310 | 0 | 1000.01 | true | 3 | 0 | PASS | — |
| W0311 | 0 | 1000.01 | true | 4 | 0 | PASS | — |
| W0312 | 0 | 1000.01 | true | 5 | 0 | PASS | — |
| W0313 | 0 | 1000.01 | true | 6 | 0 | PASS | — |
| W0314 | 0 | 1000.01 | true | 7 | 0.000 | PASS | — |
| W0315 | 0 | 1000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0316 | 0 | 1000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0317 | 0 | 1000.01 | false | 1 | 0.000 | PASS | — |
| W0318 | 0 | 1000.01 | false | 2 | 0.000 | PASS | — |
| W0319 | 0 | 1000.01 | false | 3 | 0.000 | PASS | — |
| W0320 | 0 | 1000.01 | false | 4 | 0.000 | PASS | — |
| W0321 | 0 | 1000.01 | false | 5 | 0.000 | PASS | — |
| W0322 | 0 | 1000.01 | false | 6 | 0.000 | PASS | — |
| W0323 | 0 | 1000.01 | false | 7 | 0.000 | PASS | — |
| W0324 | 0 | 1000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0325 | 0 | 4999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W0326 | 0 | 4999.99 | true | 1 | 0.000 | PASS | — |
| W0327 | 0 | 4999.99 | true | 2 | 0 | PASS | — |
| W0328 | 0 | 4999.99 | true | 3 | 0 | PASS | — |
| W0329 | 0 | 4999.99 | true | 4 | 0 | PASS | — |
| W0330 | 0 | 4999.99 | true | 5 | 0 | PASS | — |
| W0331 | 0 | 4999.99 | true | 6 | 0 | PASS | — |
| W0332 | 0 | 4999.99 | true | 7 | 0.000 | PASS | — |
| W0333 | 0 | 4999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W0334 | 0 | 4999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W0335 | 0 | 4999.99 | false | 1 | 0.000 | PASS | — |
| W0336 | 0 | 4999.99 | false | 2 | 0.000 | PASS | — |
| W0337 | 0 | 4999.99 | false | 3 | 0.000 | PASS | — |
| W0338 | 0 | 4999.99 | false | 4 | 0.000 | PASS | — |
| W0339 | 0 | 4999.99 | false | 5 | 0.000 | PASS | — |
| W0340 | 0 | 4999.99 | false | 6 | 0.000 | PASS | — |
| W0341 | 0 | 4999.99 | false | 7 | 0.000 | PASS | — |
| W0342 | 0 | 4999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W0343 | 0 | 5000 | true | 0 | REJECT | FAIL | W-INVALID |
| W0344 | 0 | 5000 | true | 1 | 0.000 | PASS | — |
| W0345 | 0 | 5000 | true | 2 | 0 | PASS | — |
| W0346 | 0 | 5000 | true | 3 | 0 | PASS | — |
| W0347 | 0 | 5000 | true | 4 | 0 | PASS | — |
| W0348 | 0 | 5000 | true | 5 | 0 | PASS | — |
| W0349 | 0 | 5000 | true | 6 | 0 | PASS | — |
| W0350 | 0 | 5000 | true | 7 | 0.000 | PASS | — |
| W0351 | 0 | 5000 | true | 8 | REJECT | FAIL | W-INVALID |
| W0352 | 0 | 5000 | false | 0 | REJECT | FAIL | W-INVALID |
| W0353 | 0 | 5000 | false | 1 | 0 | PASS | — |
| W0354 | 0 | 5000 | false | 2 | 0 | PASS | — |
| W0355 | 0 | 5000 | false | 3 | 0 | PASS | — |
| W0356 | 0 | 5000 | false | 4 | 0 | PASS | — |
| W0357 | 0 | 5000 | false | 5 | 0 | PASS | — |
| W0358 | 0 | 5000 | false | 6 | 0 | PASS | — |
| W0359 | 0 | 5000 | false | 7 | 0 | PASS | — |
| W0360 | 0 | 5000 | false | 8 | REJECT | FAIL | W-INVALID |
| W0361 | 0 | 5000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0362 | 0 | 5000.01 | true | 1 | 0.000 | PASS | — |
| W0363 | 0 | 5000.01 | true | 2 | 0 | PASS | — |
| W0364 | 0 | 5000.01 | true | 3 | 0 | PASS | — |
| W0365 | 0 | 5000.01 | true | 4 | 0 | PASS | — |
| W0366 | 0 | 5000.01 | true | 5 | 0 | PASS | — |
| W0367 | 0 | 5000.01 | true | 6 | 0 | PASS | — |
| W0368 | 0 | 5000.01 | true | 7 | 0.000 | PASS | — |
| W0369 | 0 | 5000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0370 | 0 | 5000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0371 | 0 | 5000.01 | false | 1 | 0 | PASS | — |
| W0372 | 0 | 5000.01 | false | 2 | 0 | PASS | — |
| W0373 | 0 | 5000.01 | false | 3 | 0 | PASS | — |
| W0374 | 0 | 5000.01 | false | 4 | 0 | PASS | — |
| W0375 | 0 | 5000.01 | false | 5 | 0 | PASS | — |
| W0376 | 0 | 5000.01 | false | 6 | 0 | PASS | — |
| W0377 | 0 | 5000.01 | false | 7 | 0 | PASS | — |
| W0378 | 0 | 5000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0379 | 0 | 9999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W0380 | 0 | 9999.99 | true | 1 | 0.000 | PASS | — |
| W0381 | 0 | 9999.99 | true | 2 | 0 | PASS | — |
| W0382 | 0 | 9999.99 | true | 3 | 0 | PASS | — |
| W0383 | 0 | 9999.99 | true | 4 | 0 | PASS | — |
| W0384 | 0 | 9999.99 | true | 5 | 0 | PASS | — |
| W0385 | 0 | 9999.99 | true | 6 | 0 | PASS | — |
| W0386 | 0 | 9999.99 | true | 7 | 0.000 | PASS | — |
| W0387 | 0 | 9999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W0388 | 0 | 9999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W0389 | 0 | 9999.99 | false | 1 | 0 | PASS | — |
| W0390 | 0 | 9999.99 | false | 2 | 0 | PASS | — |
| W0391 | 0 | 9999.99 | false | 3 | 0 | PASS | — |
| W0392 | 0 | 9999.99 | false | 4 | 0 | PASS | — |
| W0393 | 0 | 9999.99 | false | 5 | 0 | PASS | — |
| W0394 | 0 | 9999.99 | false | 6 | 0 | PASS | — |
| W0395 | 0 | 9999.99 | false | 7 | 0 | PASS | — |
| W0396 | 0 | 9999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W0397 | 0 | 10000 | true | 0 | REJECT | FAIL | W-INVALID |
| W0398 | 0 | 10000 | true | 1 | 0.000 | PASS | — |
| W0399 | 0 | 10000 | true | 2 | 0 | PASS | — |
| W0400 | 0 | 10000 | true | 3 | 0 | PASS | — |
| W0401 | 0 | 10000 | true | 4 | 0 | PASS | — |
| W0402 | 0 | 10000 | true | 5 | 0 | PASS | — |
| W0403 | 0 | 10000 | true | 6 | 0 | PASS | — |
| W0404 | 0 | 10000 | true | 7 | 0.000 | PASS | — |
| W0405 | 0 | 10000 | true | 8 | REJECT | FAIL | W-INVALID |
| W0406 | 0 | 10000 | false | 0 | REJECT | FAIL | W-INVALID |
| W0407 | 0 | 10000 | false | 1 | 0 | PASS | — |
| W0408 | 0 | 10000 | false | 2 | 0 | PASS | — |
| W0409 | 0 | 10000 | false | 3 | 0 | PASS | — |
| W0410 | 0 | 10000 | false | 4 | 0 | PASS | — |
| W0411 | 0 | 10000 | false | 5 | 0 | PASS | — |
| W0412 | 0 | 10000 | false | 6 | 0 | PASS | — |
| W0413 | 0 | 10000 | false | 7 | 0 | PASS | — |
| W0414 | 0 | 10000 | false | 8 | REJECT | FAIL | W-INVALID |
| W0415 | 0 | 10000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0416 | 0 | 10000.01 | true | 1 | 0.000 | PASS | — |
| W0417 | 0 | 10000.01 | true | 2 | 0 | PASS | — |
| W0418 | 0 | 10000.01 | true | 3 | 0 | PASS | — |
| W0419 | 0 | 10000.01 | true | 4 | 0 | PASS | — |
| W0420 | 0 | 10000.01 | true | 5 | 0 | PASS | — |
| W0421 | 0 | 10000.01 | true | 6 | 0 | PASS | — |
| W0422 | 0 | 10000.01 | true | 7 | 0.000 | PASS | — |
| W0423 | 0 | 10000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0424 | 0 | 10000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0425 | 0 | 10000.01 | false | 1 | 0 | PASS | — |
| W0426 | 0 | 10000.01 | false | 2 | 0 | PASS | — |
| W0427 | 0 | 10000.01 | false | 3 | 0 | PASS | — |
| W0428 | 0 | 10000.01 | false | 4 | 0 | PASS | — |
| W0429 | 0 | 10000.01 | false | 5 | 0 | PASS | — |
| W0430 | 0 | 10000.01 | false | 6 | 0 | PASS | — |
| W0431 | 0 | 10000.01 | false | 7 | 0 | PASS | — |
| W0432 | 0 | 10000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0433 | 0.01 | -0.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0434 | 0.01 | -0.01 | true | 1 | REJECT | FAIL | W-INVALID |
| W0435 | 0.01 | -0.01 | true | 2 | REJECT | FAIL | W-INVALID |
| W0436 | 0.01 | -0.01 | true | 3 | REJECT | FAIL | W-INVALID |
| W0437 | 0.01 | -0.01 | true | 4 | REJECT | FAIL | W-INVALID |
| W0438 | 0.01 | -0.01 | true | 5 | REJECT | FAIL | W-INVALID |
| W0439 | 0.01 | -0.01 | true | 6 | REJECT | FAIL | W-INVALID |
| W0440 | 0.01 | -0.01 | true | 7 | REJECT | FAIL | W-INVALID |
| W0441 | 0.01 | -0.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0442 | 0.01 | -0.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0443 | 0.01 | -0.01 | false | 1 | REJECT | FAIL | W-INVALID |
| W0444 | 0.01 | -0.01 | false | 2 | REJECT | FAIL | W-INVALID |
| W0445 | 0.01 | -0.01 | false | 3 | REJECT | FAIL | W-INVALID |
| W0446 | 0.01 | -0.01 | false | 4 | REJECT | FAIL | W-INVALID |
| W0447 | 0.01 | -0.01 | false | 5 | REJECT | FAIL | W-INVALID |
| W0448 | 0.01 | -0.01 | false | 6 | REJECT | FAIL | W-INVALID |
| W0449 | 0.01 | -0.01 | false | 7 | REJECT | FAIL | W-INVALID |
| W0450 | 0.01 | -0.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0451 | 0.01 | 0 | true | 0 | REJECT | FAIL | W-INVALID |
| W0452 | 0.01 | 0 | true | 1 | 0.00001 | FAIL | W-STUDENT |
| W0453 | 0.01 | 0 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0454 | 0.01 | 0 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0455 | 0.01 | 0 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0456 | 0.01 | 0 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0457 | 0.01 | 0 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0458 | 0.01 | 0 | true | 7 | 0.00001 | FAIL | W-STUDENT |
| W0459 | 0.01 | 0 | true | 8 | REJECT | FAIL | W-INVALID |
| W0460 | 0.01 | 0 | false | 0 | REJECT | FAIL | W-INVALID |
| W0461 | 0.01 | 0 | false | 1 | 0.00003 | FAIL | W-LOW |
| W0462 | 0.01 | 0 | false | 2 | 0.00003 | FAIL | W-LOW |
| W0463 | 0.01 | 0 | false | 3 | 0.00003 | FAIL | W-LOW |
| W0464 | 0.01 | 0 | false | 4 | 0.00003 | FAIL | W-LOW |
| W0465 | 0.01 | 0 | false | 5 | 0.00003 | FAIL | W-LOW |
| W0466 | 0.01 | 0 | false | 6 | 0.00003 | FAIL | W-LOW |
| W0467 | 0.01 | 0 | false | 7 | 0.00003 | FAIL | W-LOW |
| W0468 | 0.01 | 0 | false | 8 | REJECT | FAIL | W-INVALID |
| W0469 | 0.01 | 0.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0470 | 0.01 | 0.01 | true | 1 | 0.00001 | FAIL | W-STUDENT |
| W0471 | 0.01 | 0.01 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0472 | 0.01 | 0.01 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0473 | 0.01 | 0.01 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0474 | 0.01 | 0.01 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0475 | 0.01 | 0.01 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0476 | 0.01 | 0.01 | true | 7 | 0.00001 | FAIL | W-STUDENT |
| W0477 | 0.01 | 0.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0478 | 0.01 | 0.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0479 | 0.01 | 0.01 | false | 1 | 0.00003 | FAIL | W-LOW |
| W0480 | 0.01 | 0.01 | false | 2 | 0.00003 | FAIL | W-LOW |
| W0481 | 0.01 | 0.01 | false | 3 | 0.00003 | FAIL | W-LOW |
| W0482 | 0.01 | 0.01 | false | 4 | 0.00003 | FAIL | W-LOW |
| W0483 | 0.01 | 0.01 | false | 5 | 0.00003 | FAIL | W-LOW |
| W0484 | 0.01 | 0.01 | false | 6 | 0.00003 | FAIL | W-LOW |
| W0485 | 0.01 | 0.01 | false | 7 | 0.00003 | FAIL | W-LOW |
| W0486 | 0.01 | 0.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0487 | 0.01 | 999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W0488 | 0.01 | 999.99 | true | 1 | 0.00001 | FAIL | W-STUDENT |
| W0489 | 0.01 | 999.99 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0490 | 0.01 | 999.99 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0491 | 0.01 | 999.99 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0492 | 0.01 | 999.99 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0493 | 0.01 | 999.99 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0494 | 0.01 | 999.99 | true | 7 | 0.00001 | FAIL | W-STUDENT |
| W0495 | 0.01 | 999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W0496 | 0.01 | 999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W0497 | 0.01 | 999.99 | false | 1 | 0.00003 | FAIL | W-LOW |
| W0498 | 0.01 | 999.99 | false | 2 | 0.00003 | FAIL | W-LOW |
| W0499 | 0.01 | 999.99 | false | 3 | 0.00003 | FAIL | W-LOW |
| W0500 | 0.01 | 999.99 | false | 4 | 0.00003 | FAIL | W-LOW |
| W0501 | 0.01 | 999.99 | false | 5 | 0.00003 | FAIL | W-LOW |
| W0502 | 0.01 | 999.99 | false | 6 | 0.00003 | FAIL | W-LOW |
| W0503 | 0.01 | 999.99 | false | 7 | 0.00003 | FAIL | W-LOW |
| W0504 | 0.01 | 999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W0505 | 0.01 | 1000 | true | 0 | REJECT | FAIL | W-INVALID |
| W0506 | 0.01 | 1000 | true | 1 | 0.00001 | FAIL | W-STUDENT |
| W0507 | 0.01 | 1000 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0508 | 0.01 | 1000 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0509 | 0.01 | 1000 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0510 | 0.01 | 1000 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0511 | 0.01 | 1000 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0512 | 0.01 | 1000 | true | 7 | 0.00001 | FAIL | W-STUDENT |
| W0513 | 0.01 | 1000 | true | 8 | REJECT | FAIL | W-INVALID |
| W0514 | 0.01 | 1000 | false | 0 | REJECT | FAIL | W-INVALID |
| W0515 | 0.01 | 1000 | false | 1 | 0.00001 | PASS | — |
| W0516 | 0.01 | 1000 | false | 2 | 0.00001 | PASS | — |
| W0517 | 0.01 | 1000 | false | 3 | 0.00001 | PASS | — |
| W0518 | 0.01 | 1000 | false | 4 | 0.00001 | PASS | — |
| W0519 | 0.01 | 1000 | false | 5 | 0.00001 | PASS | — |
| W0520 | 0.01 | 1000 | false | 6 | 0.00001 | PASS | — |
| W0521 | 0.01 | 1000 | false | 7 | 0.00001 | PASS | — |
| W0522 | 0.01 | 1000 | false | 8 | REJECT | FAIL | W-INVALID |
| W0523 | 0.01 | 1000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0524 | 0.01 | 1000.01 | true | 1 | 0.00001 | FAIL | W-STUDENT |
| W0525 | 0.01 | 1000.01 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0526 | 0.01 | 1000.01 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0527 | 0.01 | 1000.01 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0528 | 0.01 | 1000.01 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0529 | 0.01 | 1000.01 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0530 | 0.01 | 1000.01 | true | 7 | 0.00001 | FAIL | W-STUDENT |
| W0531 | 0.01 | 1000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0532 | 0.01 | 1000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0533 | 0.01 | 1000.01 | false | 1 | 0.00001 | PASS | — |
| W0534 | 0.01 | 1000.01 | false | 2 | 0.00001 | PASS | — |
| W0535 | 0.01 | 1000.01 | false | 3 | 0.00001 | PASS | — |
| W0536 | 0.01 | 1000.01 | false | 4 | 0.00001 | PASS | — |
| W0537 | 0.01 | 1000.01 | false | 5 | 0.00001 | PASS | — |
| W0538 | 0.01 | 1000.01 | false | 6 | 0.00001 | PASS | — |
| W0539 | 0.01 | 1000.01 | false | 7 | 0.00001 | PASS | — |
| W0540 | 0.01 | 1000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0541 | 0.01 | 4999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W0542 | 0.01 | 4999.99 | true | 1 | 0.00001 | FAIL | W-STUDENT |
| W0543 | 0.01 | 4999.99 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0544 | 0.01 | 4999.99 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0545 | 0.01 | 4999.99 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0546 | 0.01 | 4999.99 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0547 | 0.01 | 4999.99 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0548 | 0.01 | 4999.99 | true | 7 | 0.00001 | FAIL | W-STUDENT |
| W0549 | 0.01 | 4999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W0550 | 0.01 | 4999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W0551 | 0.01 | 4999.99 | false | 1 | 0.00001 | PASS | — |
| W0552 | 0.01 | 4999.99 | false | 2 | 0.00001 | PASS | — |
| W0553 | 0.01 | 4999.99 | false | 3 | 0.00001 | PASS | — |
| W0554 | 0.01 | 4999.99 | false | 4 | 0.00001 | PASS | — |
| W0555 | 0.01 | 4999.99 | false | 5 | 0.00001 | PASS | — |
| W0556 | 0.01 | 4999.99 | false | 6 | 0.00001 | PASS | — |
| W0557 | 0.01 | 4999.99 | false | 7 | 0.00001 | PASS | — |
| W0558 | 0.01 | 4999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W0559 | 0.01 | 5000 | true | 0 | REJECT | FAIL | W-INVALID |
| W0560 | 0.01 | 5000 | true | 1 | 0.00001 | FAIL | W-STUDENT |
| W0561 | 0.01 | 5000 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0562 | 0.01 | 5000 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0563 | 0.01 | 5000 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0564 | 0.01 | 5000 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0565 | 0.01 | 5000 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0566 | 0.01 | 5000 | true | 7 | 0.00001 | FAIL | W-STUDENT |
| W0567 | 0.01 | 5000 | true | 8 | REJECT | FAIL | W-INVALID |
| W0568 | 0.01 | 5000 | false | 0 | REJECT | FAIL | W-INVALID |
| W0569 | 0.01 | 5000 | false | 1 | 0.00 | FAIL | W-HIGH |
| W0570 | 0.01 | 5000 | false | 2 | 0.00 | FAIL | W-HIGH |
| W0571 | 0.01 | 5000 | false | 3 | 0.00 | FAIL | W-HIGH |
| W0572 | 0.01 | 5000 | false | 4 | 0.00 | FAIL | W-HIGH |
| W0573 | 0.01 | 5000 | false | 5 | 0.00 | FAIL | W-HIGH |
| W0574 | 0.01 | 5000 | false | 6 | 0.00 | FAIL | W-HIGH |
| W0575 | 0.01 | 5000 | false | 7 | 0.00 | FAIL | W-HIGH |
| W0576 | 0.01 | 5000 | false | 8 | REJECT | FAIL | W-INVALID |
| W0577 | 0.01 | 5000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0578 | 0.01 | 5000.01 | true | 1 | 0.00001 | FAIL | W-STUDENT |
| W0579 | 0.01 | 5000.01 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0580 | 0.01 | 5000.01 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0581 | 0.01 | 5000.01 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0582 | 0.01 | 5000.01 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0583 | 0.01 | 5000.01 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0584 | 0.01 | 5000.01 | true | 7 | 0.00001 | FAIL | W-STUDENT |
| W0585 | 0.01 | 5000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0586 | 0.01 | 5000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0587 | 0.01 | 5000.01 | false | 1 | 0.00 | FAIL | W-HIGH |
| W0588 | 0.01 | 5000.01 | false | 2 | 0.00 | FAIL | W-HIGH |
| W0589 | 0.01 | 5000.01 | false | 3 | 0.00 | FAIL | W-HIGH |
| W0590 | 0.01 | 5000.01 | false | 4 | 0.00 | FAIL | W-HIGH |
| W0591 | 0.01 | 5000.01 | false | 5 | 0.00 | FAIL | W-HIGH |
| W0592 | 0.01 | 5000.01 | false | 6 | 0.00 | FAIL | W-HIGH |
| W0593 | 0.01 | 5000.01 | false | 7 | 0.00 | FAIL | W-HIGH |
| W0594 | 0.01 | 5000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0595 | 0.01 | 9999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W0596 | 0.01 | 9999.99 | true | 1 | 0.00001 | FAIL | W-STUDENT |
| W0597 | 0.01 | 9999.99 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0598 | 0.01 | 9999.99 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0599 | 0.01 | 9999.99 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0600 | 0.01 | 9999.99 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0601 | 0.01 | 9999.99 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0602 | 0.01 | 9999.99 | true | 7 | 0.00001 | FAIL | W-STUDENT |
| W0603 | 0.01 | 9999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W0604 | 0.01 | 9999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W0605 | 0.01 | 9999.99 | false | 1 | 0.00 | FAIL | W-HIGH |
| W0606 | 0.01 | 9999.99 | false | 2 | 0.00 | FAIL | W-HIGH |
| W0607 | 0.01 | 9999.99 | false | 3 | 0.00 | FAIL | W-HIGH |
| W0608 | 0.01 | 9999.99 | false | 4 | 0.00 | FAIL | W-HIGH |
| W0609 | 0.01 | 9999.99 | false | 5 | 0.00 | FAIL | W-HIGH |
| W0610 | 0.01 | 9999.99 | false | 6 | 0.00 | FAIL | W-HIGH |
| W0611 | 0.01 | 9999.99 | false | 7 | 0.00 | FAIL | W-HIGH |
| W0612 | 0.01 | 9999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W0613 | 0.01 | 10000 | true | 0 | REJECT | FAIL | W-INVALID |
| W0614 | 0.01 | 10000 | true | 1 | 0.00001 | FAIL | W-STUDENT |
| W0615 | 0.01 | 10000 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0616 | 0.01 | 10000 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0617 | 0.01 | 10000 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0618 | 0.01 | 10000 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0619 | 0.01 | 10000 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0620 | 0.01 | 10000 | true | 7 | 0.00001 | FAIL | W-STUDENT |
| W0621 | 0.01 | 10000 | true | 8 | REJECT | FAIL | W-INVALID |
| W0622 | 0.01 | 10000 | false | 0 | REJECT | FAIL | W-INVALID |
| W0623 | 0.01 | 10000 | false | 1 | 0.00 | PASS | — |
| W0624 | 0.01 | 10000 | false | 2 | 0.00 | PASS | — |
| W0625 | 0.01 | 10000 | false | 3 | 0.00 | PASS | — |
| W0626 | 0.01 | 10000 | false | 4 | 0.00 | PASS | — |
| W0627 | 0.01 | 10000 | false | 5 | 0.00 | PASS | — |
| W0628 | 0.01 | 10000 | false | 6 | 0.00 | PASS | — |
| W0629 | 0.01 | 10000 | false | 7 | 0.00 | PASS | — |
| W0630 | 0.01 | 10000 | false | 8 | REJECT | FAIL | W-INVALID |
| W0631 | 0.01 | 10000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0632 | 0.01 | 10000.01 | true | 1 | 0.00001 | FAIL | W-STUDENT |
| W0633 | 0.01 | 10000.01 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0634 | 0.01 | 10000.01 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0635 | 0.01 | 10000.01 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0636 | 0.01 | 10000.01 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0637 | 0.01 | 10000.01 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0638 | 0.01 | 10000.01 | true | 7 | 0.00001 | FAIL | W-STUDENT |
| W0639 | 0.01 | 10000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0640 | 0.01 | 10000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0641 | 0.01 | 10000.01 | false | 1 | 0.00 | PASS | — |
| W0642 | 0.01 | 10000.01 | false | 2 | 0.00 | PASS | — |
| W0643 | 0.01 | 10000.01 | false | 3 | 0.00 | PASS | — |
| W0644 | 0.01 | 10000.01 | false | 4 | 0.00 | PASS | — |
| W0645 | 0.01 | 10000.01 | false | 5 | 0.00 | PASS | — |
| W0646 | 0.01 | 10000.01 | false | 6 | 0.00 | PASS | — |
| W0647 | 0.01 | 10000.01 | false | 7 | 0.00 | PASS | — |
| W0648 | 0.01 | 10000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0649 | 500 | -0.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0650 | 500 | -0.01 | true | 1 | REJECT | FAIL | W-INVALID |
| W0651 | 500 | -0.01 | true | 2 | REJECT | FAIL | W-INVALID |
| W0652 | 500 | -0.01 | true | 3 | REJECT | FAIL | W-INVALID |
| W0653 | 500 | -0.01 | true | 4 | REJECT | FAIL | W-INVALID |
| W0654 | 500 | -0.01 | true | 5 | REJECT | FAIL | W-INVALID |
| W0655 | 500 | -0.01 | true | 6 | REJECT | FAIL | W-INVALID |
| W0656 | 500 | -0.01 | true | 7 | REJECT | FAIL | W-INVALID |
| W0657 | 500 | -0.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0658 | 500 | -0.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0659 | 500 | -0.01 | false | 1 | REJECT | FAIL | W-INVALID |
| W0660 | 500 | -0.01 | false | 2 | REJECT | FAIL | W-INVALID |
| W0661 | 500 | -0.01 | false | 3 | REJECT | FAIL | W-INVALID |
| W0662 | 500 | -0.01 | false | 4 | REJECT | FAIL | W-INVALID |
| W0663 | 500 | -0.01 | false | 5 | REJECT | FAIL | W-INVALID |
| W0664 | 500 | -0.01 | false | 6 | REJECT | FAIL | W-INVALID |
| W0665 | 500 | -0.01 | false | 7 | REJECT | FAIL | W-INVALID |
| W0666 | 500 | -0.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0667 | 500 | 0 | true | 0 | REJECT | FAIL | W-INVALID |
| W0668 | 500 | 0 | true | 1 | 0.500 | FAIL | W-STUDENT |
| W0669 | 500 | 0 | true | 2 | 0 | FAIL | W-STUDENT |
| W0670 | 500 | 0 | true | 3 | 0 | FAIL | W-STUDENT |
| W0671 | 500 | 0 | true | 4 | 0 | FAIL | W-STUDENT |
| W0672 | 500 | 0 | true | 5 | 0 | FAIL | W-STUDENT |
| W0673 | 500 | 0 | true | 6 | 0 | FAIL | W-STUDENT |
| W0674 | 500 | 0 | true | 7 | 0.500 | FAIL | W-STUDENT |
| W0675 | 500 | 0 | true | 8 | REJECT | FAIL | W-INVALID |
| W0676 | 500 | 0 | false | 0 | REJECT | FAIL | W-INVALID |
| W0677 | 500 | 0 | false | 1 | 1.500 | FAIL | W-LOW |
| W0678 | 500 | 0 | false | 2 | 1.500 | FAIL | W-LOW |
| W0679 | 500 | 0 | false | 3 | 1.500 | FAIL | W-LOW |
| W0680 | 500 | 0 | false | 4 | 1.500 | FAIL | W-LOW |
| W0681 | 500 | 0 | false | 5 | 1.500 | FAIL | W-LOW |
| W0682 | 500 | 0 | false | 6 | 1.500 | FAIL | W-LOW |
| W0683 | 500 | 0 | false | 7 | 1.500 | FAIL | W-LOW |
| W0684 | 500 | 0 | false | 8 | REJECT | FAIL | W-INVALID |
| W0685 | 500 | 0.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0686 | 500 | 0.01 | true | 1 | 0.500 | FAIL | W-STUDENT |
| W0687 | 500 | 0.01 | true | 2 | 0 | FAIL | W-STUDENT |
| W0688 | 500 | 0.01 | true | 3 | 0 | FAIL | W-STUDENT |
| W0689 | 500 | 0.01 | true | 4 | 0 | FAIL | W-STUDENT |
| W0690 | 500 | 0.01 | true | 5 | 0 | FAIL | W-STUDENT |
| W0691 | 500 | 0.01 | true | 6 | 0 | FAIL | W-STUDENT |
| W0692 | 500 | 0.01 | true | 7 | 0.500 | FAIL | W-STUDENT |
| W0693 | 500 | 0.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0694 | 500 | 0.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0695 | 500 | 0.01 | false | 1 | 1.500 | FAIL | W-LOW |
| W0696 | 500 | 0.01 | false | 2 | 1.500 | FAIL | W-LOW |
| W0697 | 500 | 0.01 | false | 3 | 1.500 | FAIL | W-LOW |
| W0698 | 500 | 0.01 | false | 4 | 1.500 | FAIL | W-LOW |
| W0699 | 500 | 0.01 | false | 5 | 1.500 | FAIL | W-LOW |
| W0700 | 500 | 0.01 | false | 6 | 1.500 | FAIL | W-LOW |
| W0701 | 500 | 0.01 | false | 7 | 1.500 | FAIL | W-LOW |
| W0702 | 500 | 0.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0703 | 500 | 999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W0704 | 500 | 999.99 | true | 1 | 0.500 | FAIL | W-STUDENT |
| W0705 | 500 | 999.99 | true | 2 | 0 | FAIL | W-STUDENT |
| W0706 | 500 | 999.99 | true | 3 | 0 | FAIL | W-STUDENT |
| W0707 | 500 | 999.99 | true | 4 | 0 | FAIL | W-STUDENT |
| W0708 | 500 | 999.99 | true | 5 | 0 | FAIL | W-STUDENT |
| W0709 | 500 | 999.99 | true | 6 | 0 | FAIL | W-STUDENT |
| W0710 | 500 | 999.99 | true | 7 | 0.500 | FAIL | W-STUDENT |
| W0711 | 500 | 999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W0712 | 500 | 999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W0713 | 500 | 999.99 | false | 1 | 1.500 | FAIL | W-LOW |
| W0714 | 500 | 999.99 | false | 2 | 1.500 | FAIL | W-LOW |
| W0715 | 500 | 999.99 | false | 3 | 1.500 | FAIL | W-LOW |
| W0716 | 500 | 999.99 | false | 4 | 1.500 | FAIL | W-LOW |
| W0717 | 500 | 999.99 | false | 5 | 1.500 | FAIL | W-LOW |
| W0718 | 500 | 999.99 | false | 6 | 1.500 | FAIL | W-LOW |
| W0719 | 500 | 999.99 | false | 7 | 1.500 | FAIL | W-LOW |
| W0720 | 500 | 999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W0721 | 500 | 1000 | true | 0 | REJECT | FAIL | W-INVALID |
| W0722 | 500 | 1000 | true | 1 | 0.500 | FAIL | W-STUDENT |
| W0723 | 500 | 1000 | true | 2 | 0 | FAIL | W-STUDENT |
| W0724 | 500 | 1000 | true | 3 | 0 | FAIL | W-STUDENT |
| W0725 | 500 | 1000 | true | 4 | 0 | FAIL | W-STUDENT |
| W0726 | 500 | 1000 | true | 5 | 0 | FAIL | W-STUDENT |
| W0727 | 500 | 1000 | true | 6 | 0 | FAIL | W-STUDENT |
| W0728 | 500 | 1000 | true | 7 | 0.500 | FAIL | W-STUDENT |
| W0729 | 500 | 1000 | true | 8 | REJECT | FAIL | W-INVALID |
| W0730 | 500 | 1000 | false | 0 | REJECT | FAIL | W-INVALID |
| W0731 | 500 | 1000 | false | 1 | 0.500 | PASS | — |
| W0732 | 500 | 1000 | false | 2 | 0.500 | PASS | — |
| W0733 | 500 | 1000 | false | 3 | 0.500 | PASS | — |
| W0734 | 500 | 1000 | false | 4 | 0.500 | PASS | — |
| W0735 | 500 | 1000 | false | 5 | 0.500 | PASS | — |
| W0736 | 500 | 1000 | false | 6 | 0.500 | PASS | — |
| W0737 | 500 | 1000 | false | 7 | 0.500 | PASS | — |
| W0738 | 500 | 1000 | false | 8 | REJECT | FAIL | W-INVALID |
| W0739 | 500 | 1000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0740 | 500 | 1000.01 | true | 1 | 0.500 | FAIL | W-STUDENT |
| W0741 | 500 | 1000.01 | true | 2 | 0 | FAIL | W-STUDENT |
| W0742 | 500 | 1000.01 | true | 3 | 0 | FAIL | W-STUDENT |
| W0743 | 500 | 1000.01 | true | 4 | 0 | FAIL | W-STUDENT |
| W0744 | 500 | 1000.01 | true | 5 | 0 | FAIL | W-STUDENT |
| W0745 | 500 | 1000.01 | true | 6 | 0 | FAIL | W-STUDENT |
| W0746 | 500 | 1000.01 | true | 7 | 0.500 | FAIL | W-STUDENT |
| W0747 | 500 | 1000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0748 | 500 | 1000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0749 | 500 | 1000.01 | false | 1 | 0.500 | PASS | — |
| W0750 | 500 | 1000.01 | false | 2 | 0.500 | PASS | — |
| W0751 | 500 | 1000.01 | false | 3 | 0.500 | PASS | — |
| W0752 | 500 | 1000.01 | false | 4 | 0.500 | PASS | — |
| W0753 | 500 | 1000.01 | false | 5 | 0.500 | PASS | — |
| W0754 | 500 | 1000.01 | false | 6 | 0.500 | PASS | — |
| W0755 | 500 | 1000.01 | false | 7 | 0.500 | PASS | — |
| W0756 | 500 | 1000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0757 | 500 | 4999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W0758 | 500 | 4999.99 | true | 1 | 0.500 | FAIL | W-STUDENT |
| W0759 | 500 | 4999.99 | true | 2 | 0 | FAIL | W-STUDENT |
| W0760 | 500 | 4999.99 | true | 3 | 0 | FAIL | W-STUDENT |
| W0761 | 500 | 4999.99 | true | 4 | 0 | FAIL | W-STUDENT |
| W0762 | 500 | 4999.99 | true | 5 | 0 | FAIL | W-STUDENT |
| W0763 | 500 | 4999.99 | true | 6 | 0 | FAIL | W-STUDENT |
| W0764 | 500 | 4999.99 | true | 7 | 0.500 | FAIL | W-STUDENT |
| W0765 | 500 | 4999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W0766 | 500 | 4999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W0767 | 500 | 4999.99 | false | 1 | 0.500 | PASS | — |
| W0768 | 500 | 4999.99 | false | 2 | 0.500 | PASS | — |
| W0769 | 500 | 4999.99 | false | 3 | 0.500 | PASS | — |
| W0770 | 500 | 4999.99 | false | 4 | 0.500 | PASS | — |
| W0771 | 500 | 4999.99 | false | 5 | 0.500 | PASS | — |
| W0772 | 500 | 4999.99 | false | 6 | 0.500 | PASS | — |
| W0773 | 500 | 4999.99 | false | 7 | 0.500 | PASS | — |
| W0774 | 500 | 4999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W0775 | 500 | 5000 | true | 0 | REJECT | FAIL | W-INVALID |
| W0776 | 500 | 5000 | true | 1 | 0.500 | FAIL | W-STUDENT |
| W0777 | 500 | 5000 | true | 2 | 0 | FAIL | W-STUDENT |
| W0778 | 500 | 5000 | true | 3 | 0 | FAIL | W-STUDENT |
| W0779 | 500 | 5000 | true | 4 | 0 | FAIL | W-STUDENT |
| W0780 | 500 | 5000 | true | 5 | 0 | FAIL | W-STUDENT |
| W0781 | 500 | 5000 | true | 6 | 0 | FAIL | W-STUDENT |
| W0782 | 500 | 5000 | true | 7 | 0.500 | FAIL | W-STUDENT |
| W0783 | 500 | 5000 | true | 8 | REJECT | FAIL | W-INVALID |
| W0784 | 500 | 5000 | false | 0 | REJECT | FAIL | W-INVALID |
| W0785 | 500 | 5000 | false | 1 | 0 | FAIL | W-HIGH |
| W0786 | 500 | 5000 | false | 2 | 0 | FAIL | W-HIGH |
| W0787 | 500 | 5000 | false | 3 | 0 | FAIL | W-HIGH |
| W0788 | 500 | 5000 | false | 4 | 0 | FAIL | W-HIGH |
| W0789 | 500 | 5000 | false | 5 | 0 | FAIL | W-HIGH |
| W0790 | 500 | 5000 | false | 6 | 0 | FAIL | W-HIGH |
| W0791 | 500 | 5000 | false | 7 | 0 | FAIL | W-HIGH |
| W0792 | 500 | 5000 | false | 8 | REJECT | FAIL | W-INVALID |
| W0793 | 500 | 5000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0794 | 500 | 5000.01 | true | 1 | 0.500 | FAIL | W-STUDENT |
| W0795 | 500 | 5000.01 | true | 2 | 0 | FAIL | W-STUDENT |
| W0796 | 500 | 5000.01 | true | 3 | 0 | FAIL | W-STUDENT |
| W0797 | 500 | 5000.01 | true | 4 | 0 | FAIL | W-STUDENT |
| W0798 | 500 | 5000.01 | true | 5 | 0 | FAIL | W-STUDENT |
| W0799 | 500 | 5000.01 | true | 6 | 0 | FAIL | W-STUDENT |
| W0800 | 500 | 5000.01 | true | 7 | 0.500 | FAIL | W-STUDENT |
| W0801 | 500 | 5000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0802 | 500 | 5000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0803 | 500 | 5000.01 | false | 1 | 0 | FAIL | W-HIGH |
| W0804 | 500 | 5000.01 | false | 2 | 0 | FAIL | W-HIGH |
| W0805 | 500 | 5000.01 | false | 3 | 0 | FAIL | W-HIGH |
| W0806 | 500 | 5000.01 | false | 4 | 0 | FAIL | W-HIGH |
| W0807 | 500 | 5000.01 | false | 5 | 0 | FAIL | W-HIGH |
| W0808 | 500 | 5000.01 | false | 6 | 0 | FAIL | W-HIGH |
| W0809 | 500 | 5000.01 | false | 7 | 0 | FAIL | W-HIGH |
| W0810 | 500 | 5000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0811 | 500 | 9999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W0812 | 500 | 9999.99 | true | 1 | 0.500 | FAIL | W-STUDENT |
| W0813 | 500 | 9999.99 | true | 2 | 0 | FAIL | W-STUDENT |
| W0814 | 500 | 9999.99 | true | 3 | 0 | FAIL | W-STUDENT |
| W0815 | 500 | 9999.99 | true | 4 | 0 | FAIL | W-STUDENT |
| W0816 | 500 | 9999.99 | true | 5 | 0 | FAIL | W-STUDENT |
| W0817 | 500 | 9999.99 | true | 6 | 0 | FAIL | W-STUDENT |
| W0818 | 500 | 9999.99 | true | 7 | 0.500 | FAIL | W-STUDENT |
| W0819 | 500 | 9999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W0820 | 500 | 9999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W0821 | 500 | 9999.99 | false | 1 | 0 | FAIL | W-HIGH |
| W0822 | 500 | 9999.99 | false | 2 | 0 | FAIL | W-HIGH |
| W0823 | 500 | 9999.99 | false | 3 | 0 | FAIL | W-HIGH |
| W0824 | 500 | 9999.99 | false | 4 | 0 | FAIL | W-HIGH |
| W0825 | 500 | 9999.99 | false | 5 | 0 | FAIL | W-HIGH |
| W0826 | 500 | 9999.99 | false | 6 | 0 | FAIL | W-HIGH |
| W0827 | 500 | 9999.99 | false | 7 | 0 | FAIL | W-HIGH |
| W0828 | 500 | 9999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W0829 | 500 | 10000 | true | 0 | REJECT | FAIL | W-INVALID |
| W0830 | 500 | 10000 | true | 1 | 0.500 | FAIL | W-STUDENT |
| W0831 | 500 | 10000 | true | 2 | 0 | FAIL | W-STUDENT |
| W0832 | 500 | 10000 | true | 3 | 0 | FAIL | W-STUDENT |
| W0833 | 500 | 10000 | true | 4 | 0 | FAIL | W-STUDENT |
| W0834 | 500 | 10000 | true | 5 | 0 | FAIL | W-STUDENT |
| W0835 | 500 | 10000 | true | 6 | 0 | FAIL | W-STUDENT |
| W0836 | 500 | 10000 | true | 7 | 0.500 | FAIL | W-STUDENT |
| W0837 | 500 | 10000 | true | 8 | REJECT | FAIL | W-INVALID |
| W0838 | 500 | 10000 | false | 0 | REJECT | FAIL | W-INVALID |
| W0839 | 500 | 10000 | false | 1 | 0 | PASS | — |
| W0840 | 500 | 10000 | false | 2 | 0 | PASS | — |
| W0841 | 500 | 10000 | false | 3 | 0 | PASS | — |
| W0842 | 500 | 10000 | false | 4 | 0 | PASS | — |
| W0843 | 500 | 10000 | false | 5 | 0 | PASS | — |
| W0844 | 500 | 10000 | false | 6 | 0 | PASS | — |
| W0845 | 500 | 10000 | false | 7 | 0 | PASS | — |
| W0846 | 500 | 10000 | false | 8 | REJECT | FAIL | W-INVALID |
| W0847 | 500 | 10000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0848 | 500 | 10000.01 | true | 1 | 0.500 | FAIL | W-STUDENT |
| W0849 | 500 | 10000.01 | true | 2 | 0 | FAIL | W-STUDENT |
| W0850 | 500 | 10000.01 | true | 3 | 0 | FAIL | W-STUDENT |
| W0851 | 500 | 10000.01 | true | 4 | 0 | FAIL | W-STUDENT |
| W0852 | 500 | 10000.01 | true | 5 | 0 | FAIL | W-STUDENT |
| W0853 | 500 | 10000.01 | true | 6 | 0 | FAIL | W-STUDENT |
| W0854 | 500 | 10000.01 | true | 7 | 0.500 | FAIL | W-STUDENT |
| W0855 | 500 | 10000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0856 | 500 | 10000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0857 | 500 | 10000.01 | false | 1 | 0 | PASS | — |
| W0858 | 500 | 10000.01 | false | 2 | 0 | PASS | — |
| W0859 | 500 | 10000.01 | false | 3 | 0 | PASS | — |
| W0860 | 500 | 10000.01 | false | 4 | 0 | PASS | — |
| W0861 | 500 | 10000.01 | false | 5 | 0 | PASS | — |
| W0862 | 500 | 10000.01 | false | 6 | 0 | PASS | — |
| W0863 | 500 | 10000.01 | false | 7 | 0 | PASS | — |
| W0864 | 500 | 10000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0865 | 999.99 | -0.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0866 | 999.99 | -0.01 | true | 1 | REJECT | FAIL | W-INVALID |
| W0867 | 999.99 | -0.01 | true | 2 | REJECT | FAIL | W-INVALID |
| W0868 | 999.99 | -0.01 | true | 3 | REJECT | FAIL | W-INVALID |
| W0869 | 999.99 | -0.01 | true | 4 | REJECT | FAIL | W-INVALID |
| W0870 | 999.99 | -0.01 | true | 5 | REJECT | FAIL | W-INVALID |
| W0871 | 999.99 | -0.01 | true | 6 | REJECT | FAIL | W-INVALID |
| W0872 | 999.99 | -0.01 | true | 7 | REJECT | FAIL | W-INVALID |
| W0873 | 999.99 | -0.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0874 | 999.99 | -0.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0875 | 999.99 | -0.01 | false | 1 | REJECT | FAIL | W-INVALID |
| W0876 | 999.99 | -0.01 | false | 2 | REJECT | FAIL | W-INVALID |
| W0877 | 999.99 | -0.01 | false | 3 | REJECT | FAIL | W-INVALID |
| W0878 | 999.99 | -0.01 | false | 4 | REJECT | FAIL | W-INVALID |
| W0879 | 999.99 | -0.01 | false | 5 | REJECT | FAIL | W-INVALID |
| W0880 | 999.99 | -0.01 | false | 6 | REJECT | FAIL | W-INVALID |
| W0881 | 999.99 | -0.01 | false | 7 | REJECT | FAIL | W-INVALID |
| W0882 | 999.99 | -0.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0883 | 999.99 | 0 | true | 0 | REJECT | FAIL | W-INVALID |
| W0884 | 999.99 | 0 | true | 1 | 0.99999 | FAIL | W-STUDENT |
| W0885 | 999.99 | 0 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0886 | 999.99 | 0 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0887 | 999.99 | 0 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0888 | 999.99 | 0 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0889 | 999.99 | 0 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0890 | 999.99 | 0 | true | 7 | 0.99999 | FAIL | W-STUDENT |
| W0891 | 999.99 | 0 | true | 8 | REJECT | FAIL | W-INVALID |
| W0892 | 999.99 | 0 | false | 0 | REJECT | FAIL | W-INVALID |
| W0893 | 999.99 | 0 | false | 1 | 2.99997 | FAIL | W-LOW |
| W0894 | 999.99 | 0 | false | 2 | 2.99997 | FAIL | W-LOW |
| W0895 | 999.99 | 0 | false | 3 | 2.99997 | FAIL | W-LOW |
| W0896 | 999.99 | 0 | false | 4 | 2.99997 | FAIL | W-LOW |
| W0897 | 999.99 | 0 | false | 5 | 2.99997 | FAIL | W-LOW |
| W0898 | 999.99 | 0 | false | 6 | 2.99997 | FAIL | W-LOW |
| W0899 | 999.99 | 0 | false | 7 | 2.99997 | FAIL | W-LOW |
| W0900 | 999.99 | 0 | false | 8 | REJECT | FAIL | W-INVALID |
| W0901 | 999.99 | 0.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0902 | 999.99 | 0.01 | true | 1 | 0.99999 | FAIL | W-STUDENT |
| W0903 | 999.99 | 0.01 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0904 | 999.99 | 0.01 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0905 | 999.99 | 0.01 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0906 | 999.99 | 0.01 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0907 | 999.99 | 0.01 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0908 | 999.99 | 0.01 | true | 7 | 0.99999 | FAIL | W-STUDENT |
| W0909 | 999.99 | 0.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0910 | 999.99 | 0.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0911 | 999.99 | 0.01 | false | 1 | 2.99997 | FAIL | W-LOW |
| W0912 | 999.99 | 0.01 | false | 2 | 2.99997 | FAIL | W-LOW |
| W0913 | 999.99 | 0.01 | false | 3 | 2.99997 | FAIL | W-LOW |
| W0914 | 999.99 | 0.01 | false | 4 | 2.99997 | FAIL | W-LOW |
| W0915 | 999.99 | 0.01 | false | 5 | 2.99997 | FAIL | W-LOW |
| W0916 | 999.99 | 0.01 | false | 6 | 2.99997 | FAIL | W-LOW |
| W0917 | 999.99 | 0.01 | false | 7 | 2.99997 | FAIL | W-LOW |
| W0918 | 999.99 | 0.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0919 | 999.99 | 999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W0920 | 999.99 | 999.99 | true | 1 | 0.99999 | FAIL | W-STUDENT |
| W0921 | 999.99 | 999.99 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0922 | 999.99 | 999.99 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0923 | 999.99 | 999.99 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0924 | 999.99 | 999.99 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0925 | 999.99 | 999.99 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0926 | 999.99 | 999.99 | true | 7 | 0.99999 | FAIL | W-STUDENT |
| W0927 | 999.99 | 999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W0928 | 999.99 | 999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W0929 | 999.99 | 999.99 | false | 1 | 2.99997 | FAIL | W-LOW |
| W0930 | 999.99 | 999.99 | false | 2 | 2.99997 | FAIL | W-LOW |
| W0931 | 999.99 | 999.99 | false | 3 | 2.99997 | FAIL | W-LOW |
| W0932 | 999.99 | 999.99 | false | 4 | 2.99997 | FAIL | W-LOW |
| W0933 | 999.99 | 999.99 | false | 5 | 2.99997 | FAIL | W-LOW |
| W0934 | 999.99 | 999.99 | false | 6 | 2.99997 | FAIL | W-LOW |
| W0935 | 999.99 | 999.99 | false | 7 | 2.99997 | FAIL | W-LOW |
| W0936 | 999.99 | 999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W0937 | 999.99 | 1000 | true | 0 | REJECT | FAIL | W-INVALID |
| W0938 | 999.99 | 1000 | true | 1 | 0.99999 | FAIL | W-STUDENT |
| W0939 | 999.99 | 1000 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0940 | 999.99 | 1000 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0941 | 999.99 | 1000 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0942 | 999.99 | 1000 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0943 | 999.99 | 1000 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0944 | 999.99 | 1000 | true | 7 | 0.99999 | FAIL | W-STUDENT |
| W0945 | 999.99 | 1000 | true | 8 | REJECT | FAIL | W-INVALID |
| W0946 | 999.99 | 1000 | false | 0 | REJECT | FAIL | W-INVALID |
| W0947 | 999.99 | 1000 | false | 1 | 0.99999 | PASS | — |
| W0948 | 999.99 | 1000 | false | 2 | 0.99999 | PASS | — |
| W0949 | 999.99 | 1000 | false | 3 | 0.99999 | PASS | — |
| W0950 | 999.99 | 1000 | false | 4 | 0.99999 | PASS | — |
| W0951 | 999.99 | 1000 | false | 5 | 0.99999 | PASS | — |
| W0952 | 999.99 | 1000 | false | 6 | 0.99999 | PASS | — |
| W0953 | 999.99 | 1000 | false | 7 | 0.99999 | PASS | — |
| W0954 | 999.99 | 1000 | false | 8 | REJECT | FAIL | W-INVALID |
| W0955 | 999.99 | 1000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W0956 | 999.99 | 1000.01 | true | 1 | 0.99999 | FAIL | W-STUDENT |
| W0957 | 999.99 | 1000.01 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0958 | 999.99 | 1000.01 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0959 | 999.99 | 1000.01 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0960 | 999.99 | 1000.01 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0961 | 999.99 | 1000.01 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0962 | 999.99 | 1000.01 | true | 7 | 0.99999 | FAIL | W-STUDENT |
| W0963 | 999.99 | 1000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W0964 | 999.99 | 1000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W0965 | 999.99 | 1000.01 | false | 1 | 0.99999 | PASS | — |
| W0966 | 999.99 | 1000.01 | false | 2 | 0.99999 | PASS | — |
| W0967 | 999.99 | 1000.01 | false | 3 | 0.99999 | PASS | — |
| W0968 | 999.99 | 1000.01 | false | 4 | 0.99999 | PASS | — |
| W0969 | 999.99 | 1000.01 | false | 5 | 0.99999 | PASS | — |
| W0970 | 999.99 | 1000.01 | false | 6 | 0.99999 | PASS | — |
| W0971 | 999.99 | 1000.01 | false | 7 | 0.99999 | PASS | — |
| W0972 | 999.99 | 1000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W0973 | 999.99 | 4999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W0974 | 999.99 | 4999.99 | true | 1 | 0.99999 | FAIL | W-STUDENT |
| W0975 | 999.99 | 4999.99 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0976 | 999.99 | 4999.99 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0977 | 999.99 | 4999.99 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0978 | 999.99 | 4999.99 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0979 | 999.99 | 4999.99 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0980 | 999.99 | 4999.99 | true | 7 | 0.99999 | FAIL | W-STUDENT |
| W0981 | 999.99 | 4999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W0982 | 999.99 | 4999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W0983 | 999.99 | 4999.99 | false | 1 | 0.99999 | PASS | — |
| W0984 | 999.99 | 4999.99 | false | 2 | 0.99999 | PASS | — |
| W0985 | 999.99 | 4999.99 | false | 3 | 0.99999 | PASS | — |
| W0986 | 999.99 | 4999.99 | false | 4 | 0.99999 | PASS | — |
| W0987 | 999.99 | 4999.99 | false | 5 | 0.99999 | PASS | — |
| W0988 | 999.99 | 4999.99 | false | 6 | 0.99999 | PASS | — |
| W0989 | 999.99 | 4999.99 | false | 7 | 0.99999 | PASS | — |
| W0990 | 999.99 | 4999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W0991 | 999.99 | 5000 | true | 0 | REJECT | FAIL | W-INVALID |
| W0992 | 999.99 | 5000 | true | 1 | 0.99999 | FAIL | W-STUDENT |
| W0993 | 999.99 | 5000 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W0994 | 999.99 | 5000 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W0995 | 999.99 | 5000 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W0996 | 999.99 | 5000 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W0997 | 999.99 | 5000 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W0998 | 999.99 | 5000 | true | 7 | 0.99999 | FAIL | W-STUDENT |
| W0999 | 999.99 | 5000 | true | 8 | REJECT | FAIL | W-INVALID |
| W1000 | 999.99 | 5000 | false | 0 | REJECT | FAIL | W-INVALID |
| W1001 | 999.99 | 5000 | false | 1 | 0.00 | FAIL | W-HIGH |
| W1002 | 999.99 | 5000 | false | 2 | 0.00 | FAIL | W-HIGH |
| W1003 | 999.99 | 5000 | false | 3 | 0.00 | FAIL | W-HIGH |
| W1004 | 999.99 | 5000 | false | 4 | 0.00 | FAIL | W-HIGH |
| W1005 | 999.99 | 5000 | false | 5 | 0.00 | FAIL | W-HIGH |
| W1006 | 999.99 | 5000 | false | 6 | 0.00 | FAIL | W-HIGH |
| W1007 | 999.99 | 5000 | false | 7 | 0.00 | FAIL | W-HIGH |
| W1008 | 999.99 | 5000 | false | 8 | REJECT | FAIL | W-INVALID |
| W1009 | 999.99 | 5000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W1010 | 999.99 | 5000.01 | true | 1 | 0.99999 | FAIL | W-STUDENT |
| W1011 | 999.99 | 5000.01 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W1012 | 999.99 | 5000.01 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W1013 | 999.99 | 5000.01 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W1014 | 999.99 | 5000.01 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W1015 | 999.99 | 5000.01 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W1016 | 999.99 | 5000.01 | true | 7 | 0.99999 | FAIL | W-STUDENT |
| W1017 | 999.99 | 5000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W1018 | 999.99 | 5000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W1019 | 999.99 | 5000.01 | false | 1 | 0.00 | FAIL | W-HIGH |
| W1020 | 999.99 | 5000.01 | false | 2 | 0.00 | FAIL | W-HIGH |
| W1021 | 999.99 | 5000.01 | false | 3 | 0.00 | FAIL | W-HIGH |
| W1022 | 999.99 | 5000.01 | false | 4 | 0.00 | FAIL | W-HIGH |
| W1023 | 999.99 | 5000.01 | false | 5 | 0.00 | FAIL | W-HIGH |
| W1024 | 999.99 | 5000.01 | false | 6 | 0.00 | FAIL | W-HIGH |
| W1025 | 999.99 | 5000.01 | false | 7 | 0.00 | FAIL | W-HIGH |
| W1026 | 999.99 | 5000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W1027 | 999.99 | 9999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W1028 | 999.99 | 9999.99 | true | 1 | 0.99999 | FAIL | W-STUDENT |
| W1029 | 999.99 | 9999.99 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W1030 | 999.99 | 9999.99 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W1031 | 999.99 | 9999.99 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W1032 | 999.99 | 9999.99 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W1033 | 999.99 | 9999.99 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W1034 | 999.99 | 9999.99 | true | 7 | 0.99999 | FAIL | W-STUDENT |
| W1035 | 999.99 | 9999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W1036 | 999.99 | 9999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W1037 | 999.99 | 9999.99 | false | 1 | 0.00 | FAIL | W-HIGH |
| W1038 | 999.99 | 9999.99 | false | 2 | 0.00 | FAIL | W-HIGH |
| W1039 | 999.99 | 9999.99 | false | 3 | 0.00 | FAIL | W-HIGH |
| W1040 | 999.99 | 9999.99 | false | 4 | 0.00 | FAIL | W-HIGH |
| W1041 | 999.99 | 9999.99 | false | 5 | 0.00 | FAIL | W-HIGH |
| W1042 | 999.99 | 9999.99 | false | 6 | 0.00 | FAIL | W-HIGH |
| W1043 | 999.99 | 9999.99 | false | 7 | 0.00 | FAIL | W-HIGH |
| W1044 | 999.99 | 9999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W1045 | 999.99 | 10000 | true | 0 | REJECT | FAIL | W-INVALID |
| W1046 | 999.99 | 10000 | true | 1 | 0.99999 | FAIL | W-STUDENT |
| W1047 | 999.99 | 10000 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W1048 | 999.99 | 10000 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W1049 | 999.99 | 10000 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W1050 | 999.99 | 10000 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W1051 | 999.99 | 10000 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W1052 | 999.99 | 10000 | true | 7 | 0.99999 | FAIL | W-STUDENT |
| W1053 | 999.99 | 10000 | true | 8 | REJECT | FAIL | W-INVALID |
| W1054 | 999.99 | 10000 | false | 0 | REJECT | FAIL | W-INVALID |
| W1055 | 999.99 | 10000 | false | 1 | 0.00 | PASS | — |
| W1056 | 999.99 | 10000 | false | 2 | 0.00 | PASS | — |
| W1057 | 999.99 | 10000 | false | 3 | 0.00 | PASS | — |
| W1058 | 999.99 | 10000 | false | 4 | 0.00 | PASS | — |
| W1059 | 999.99 | 10000 | false | 5 | 0.00 | PASS | — |
| W1060 | 999.99 | 10000 | false | 6 | 0.00 | PASS | — |
| W1061 | 999.99 | 10000 | false | 7 | 0.00 | PASS | — |
| W1062 | 999.99 | 10000 | false | 8 | REJECT | FAIL | W-INVALID |
| W1063 | 999.99 | 10000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W1064 | 999.99 | 10000.01 | true | 1 | 0.99999 | FAIL | W-STUDENT |
| W1065 | 999.99 | 10000.01 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W1066 | 999.99 | 10000.01 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W1067 | 999.99 | 10000.01 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W1068 | 999.99 | 10000.01 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W1069 | 999.99 | 10000.01 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W1070 | 999.99 | 10000.01 | true | 7 | 0.99999 | FAIL | W-STUDENT |
| W1071 | 999.99 | 10000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W1072 | 999.99 | 10000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W1073 | 999.99 | 10000.01 | false | 1 | 0.00 | PASS | — |
| W1074 | 999.99 | 10000.01 | false | 2 | 0.00 | PASS | — |
| W1075 | 999.99 | 10000.01 | false | 3 | 0.00 | PASS | — |
| W1076 | 999.99 | 10000.01 | false | 4 | 0.00 | PASS | — |
| W1077 | 999.99 | 10000.01 | false | 5 | 0.00 | PASS | — |
| W1078 | 999.99 | 10000.01 | false | 6 | 0.00 | PASS | — |
| W1079 | 999.99 | 10000.01 | false | 7 | 0.00 | PASS | — |
| W1080 | 999.99 | 10000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W1081 | 1000 | -0.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W1082 | 1000 | -0.01 | true | 1 | REJECT | FAIL | W-INVALID |
| W1083 | 1000 | -0.01 | true | 2 | REJECT | FAIL | W-INVALID |
| W1084 | 1000 | -0.01 | true | 3 | REJECT | FAIL | W-INVALID |
| W1085 | 1000 | -0.01 | true | 4 | REJECT | FAIL | W-INVALID |
| W1086 | 1000 | -0.01 | true | 5 | REJECT | FAIL | W-INVALID |
| W1087 | 1000 | -0.01 | true | 6 | REJECT | FAIL | W-INVALID |
| W1088 | 1000 | -0.01 | true | 7 | REJECT | FAIL | W-INVALID |
| W1089 | 1000 | -0.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W1090 | 1000 | -0.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W1091 | 1000 | -0.01 | false | 1 | REJECT | FAIL | W-INVALID |
| W1092 | 1000 | -0.01 | false | 2 | REJECT | FAIL | W-INVALID |
| W1093 | 1000 | -0.01 | false | 3 | REJECT | FAIL | W-INVALID |
| W1094 | 1000 | -0.01 | false | 4 | REJECT | FAIL | W-INVALID |
| W1095 | 1000 | -0.01 | false | 5 | REJECT | FAIL | W-INVALID |
| W1096 | 1000 | -0.01 | false | 6 | REJECT | FAIL | W-INVALID |
| W1097 | 1000 | -0.01 | false | 7 | REJECT | FAIL | W-INVALID |
| W1098 | 1000 | -0.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W1099 | 1000 | 0 | true | 0 | REJECT | FAIL | W-INVALID |
| W1100 | 1000 | 0 | true | 1 | 1.000 | FAIL | W-STUDENT |
| W1101 | 1000 | 0 | true | 2 | 0 | FAIL | W-STUDENT |
| W1102 | 1000 | 0 | true | 3 | 0 | FAIL | W-STUDENT |
| W1103 | 1000 | 0 | true | 4 | 0 | FAIL | W-STUDENT |
| W1104 | 1000 | 0 | true | 5 | 0 | FAIL | W-STUDENT |
| W1105 | 1000 | 0 | true | 6 | 0 | FAIL | W-STUDENT |
| W1106 | 1000 | 0 | true | 7 | 1.000 | FAIL | W-STUDENT |
| W1107 | 1000 | 0 | true | 8 | REJECT | FAIL | W-INVALID |
| W1108 | 1000 | 0 | false | 0 | REJECT | FAIL | W-INVALID |
| W1109 | 1000 | 0 | false | 1 | 3.000 | FAIL | W-LOW |
| W1110 | 1000 | 0 | false | 2 | 3.000 | FAIL | W-LOW |
| W1111 | 1000 | 0 | false | 3 | 3.000 | FAIL | W-LOW |
| W1112 | 1000 | 0 | false | 4 | 3.000 | FAIL | W-LOW |
| W1113 | 1000 | 0 | false | 5 | 3.000 | FAIL | W-LOW |
| W1114 | 1000 | 0 | false | 6 | 3.000 | FAIL | W-LOW |
| W1115 | 1000 | 0 | false | 7 | 3.000 | FAIL | W-LOW |
| W1116 | 1000 | 0 | false | 8 | REJECT | FAIL | W-INVALID |
| W1117 | 1000 | 0.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W1118 | 1000 | 0.01 | true | 1 | 1.000 | FAIL | W-STUDENT |
| W1119 | 1000 | 0.01 | true | 2 | 0 | FAIL | W-STUDENT |
| W1120 | 1000 | 0.01 | true | 3 | 0 | FAIL | W-STUDENT |
| W1121 | 1000 | 0.01 | true | 4 | 0 | FAIL | W-STUDENT |
| W1122 | 1000 | 0.01 | true | 5 | 0 | FAIL | W-STUDENT |
| W1123 | 1000 | 0.01 | true | 6 | 0 | FAIL | W-STUDENT |
| W1124 | 1000 | 0.01 | true | 7 | 1.000 | FAIL | W-STUDENT |
| W1125 | 1000 | 0.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W1126 | 1000 | 0.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W1127 | 1000 | 0.01 | false | 1 | 3.000 | FAIL | W-LOW |
| W1128 | 1000 | 0.01 | false | 2 | 3.000 | FAIL | W-LOW |
| W1129 | 1000 | 0.01 | false | 3 | 3.000 | FAIL | W-LOW |
| W1130 | 1000 | 0.01 | false | 4 | 3.000 | FAIL | W-LOW |
| W1131 | 1000 | 0.01 | false | 5 | 3.000 | FAIL | W-LOW |
| W1132 | 1000 | 0.01 | false | 6 | 3.000 | FAIL | W-LOW |
| W1133 | 1000 | 0.01 | false | 7 | 3.000 | FAIL | W-LOW |
| W1134 | 1000 | 0.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W1135 | 1000 | 999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W1136 | 1000 | 999.99 | true | 1 | 1.000 | FAIL | W-STUDENT |
| W1137 | 1000 | 999.99 | true | 2 | 0 | FAIL | W-STUDENT |
| W1138 | 1000 | 999.99 | true | 3 | 0 | FAIL | W-STUDENT |
| W1139 | 1000 | 999.99 | true | 4 | 0 | FAIL | W-STUDENT |
| W1140 | 1000 | 999.99 | true | 5 | 0 | FAIL | W-STUDENT |
| W1141 | 1000 | 999.99 | true | 6 | 0 | FAIL | W-STUDENT |
| W1142 | 1000 | 999.99 | true | 7 | 1.000 | FAIL | W-STUDENT |
| W1143 | 1000 | 999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W1144 | 1000 | 999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W1145 | 1000 | 999.99 | false | 1 | 3.000 | FAIL | W-LOW |
| W1146 | 1000 | 999.99 | false | 2 | 3.000 | FAIL | W-LOW |
| W1147 | 1000 | 999.99 | false | 3 | 3.000 | FAIL | W-LOW |
| W1148 | 1000 | 999.99 | false | 4 | 3.000 | FAIL | W-LOW |
| W1149 | 1000 | 999.99 | false | 5 | 3.000 | FAIL | W-LOW |
| W1150 | 1000 | 999.99 | false | 6 | 3.000 | FAIL | W-LOW |
| W1151 | 1000 | 999.99 | false | 7 | 3.000 | FAIL | W-LOW |
| W1152 | 1000 | 999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W1153 | 1000 | 1000 | true | 0 | REJECT | FAIL | W-INVALID |
| W1154 | 1000 | 1000 | true | 1 | 1.000 | FAIL | W-STUDENT |
| W1155 | 1000 | 1000 | true | 2 | 0 | FAIL | W-STUDENT |
| W1156 | 1000 | 1000 | true | 3 | 0 | FAIL | W-STUDENT |
| W1157 | 1000 | 1000 | true | 4 | 0 | FAIL | W-STUDENT |
| W1158 | 1000 | 1000 | true | 5 | 0 | FAIL | W-STUDENT |
| W1159 | 1000 | 1000 | true | 6 | 0 | FAIL | W-STUDENT |
| W1160 | 1000 | 1000 | true | 7 | 1.000 | FAIL | W-STUDENT |
| W1161 | 1000 | 1000 | true | 8 | REJECT | FAIL | W-INVALID |
| W1162 | 1000 | 1000 | false | 0 | REJECT | FAIL | W-INVALID |
| W1163 | 1000 | 1000 | false | 1 | 1.000 | PASS | — |
| W1164 | 1000 | 1000 | false | 2 | 1.000 | PASS | — |
| W1165 | 1000 | 1000 | false | 3 | 1.000 | PASS | — |
| W1166 | 1000 | 1000 | false | 4 | 1.000 | PASS | — |
| W1167 | 1000 | 1000 | false | 5 | 1.000 | PASS | — |
| W1168 | 1000 | 1000 | false | 6 | 1.000 | PASS | — |
| W1169 | 1000 | 1000 | false | 7 | 1.000 | PASS | — |
| W1170 | 1000 | 1000 | false | 8 | REJECT | FAIL | W-INVALID |
| W1171 | 1000 | 1000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W1172 | 1000 | 1000.01 | true | 1 | 1.000 | FAIL | W-STUDENT |
| W1173 | 1000 | 1000.01 | true | 2 | 0 | FAIL | W-STUDENT |
| W1174 | 1000 | 1000.01 | true | 3 | 0 | FAIL | W-STUDENT |
| W1175 | 1000 | 1000.01 | true | 4 | 0 | FAIL | W-STUDENT |
| W1176 | 1000 | 1000.01 | true | 5 | 0 | FAIL | W-STUDENT |
| W1177 | 1000 | 1000.01 | true | 6 | 0 | FAIL | W-STUDENT |
| W1178 | 1000 | 1000.01 | true | 7 | 1.000 | FAIL | W-STUDENT |
| W1179 | 1000 | 1000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W1180 | 1000 | 1000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W1181 | 1000 | 1000.01 | false | 1 | 1.000 | PASS | — |
| W1182 | 1000 | 1000.01 | false | 2 | 1.000 | PASS | — |
| W1183 | 1000 | 1000.01 | false | 3 | 1.000 | PASS | — |
| W1184 | 1000 | 1000.01 | false | 4 | 1.000 | PASS | — |
| W1185 | 1000 | 1000.01 | false | 5 | 1.000 | PASS | — |
| W1186 | 1000 | 1000.01 | false | 6 | 1.000 | PASS | — |
| W1187 | 1000 | 1000.01 | false | 7 | 1.000 | PASS | — |
| W1188 | 1000 | 1000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W1189 | 1000 | 4999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W1190 | 1000 | 4999.99 | true | 1 | 1.000 | FAIL | W-STUDENT |
| W1191 | 1000 | 4999.99 | true | 2 | 0 | FAIL | W-STUDENT |
| W1192 | 1000 | 4999.99 | true | 3 | 0 | FAIL | W-STUDENT |
| W1193 | 1000 | 4999.99 | true | 4 | 0 | FAIL | W-STUDENT |
| W1194 | 1000 | 4999.99 | true | 5 | 0 | FAIL | W-STUDENT |
| W1195 | 1000 | 4999.99 | true | 6 | 0 | FAIL | W-STUDENT |
| W1196 | 1000 | 4999.99 | true | 7 | 1.000 | FAIL | W-STUDENT |
| W1197 | 1000 | 4999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W1198 | 1000 | 4999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W1199 | 1000 | 4999.99 | false | 1 | 1.000 | PASS | — |
| W1200 | 1000 | 4999.99 | false | 2 | 1.000 | PASS | — |
| W1201 | 1000 | 4999.99 | false | 3 | 1.000 | PASS | — |
| W1202 | 1000 | 4999.99 | false | 4 | 1.000 | PASS | — |
| W1203 | 1000 | 4999.99 | false | 5 | 1.000 | PASS | — |
| W1204 | 1000 | 4999.99 | false | 6 | 1.000 | PASS | — |
| W1205 | 1000 | 4999.99 | false | 7 | 1.000 | PASS | — |
| W1206 | 1000 | 4999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W1207 | 1000 | 5000 | true | 0 | REJECT | FAIL | W-INVALID |
| W1208 | 1000 | 5000 | true | 1 | 1.000 | FAIL | W-STUDENT |
| W1209 | 1000 | 5000 | true | 2 | 0 | FAIL | W-STUDENT |
| W1210 | 1000 | 5000 | true | 3 | 0 | FAIL | W-STUDENT |
| W1211 | 1000 | 5000 | true | 4 | 0 | FAIL | W-STUDENT |
| W1212 | 1000 | 5000 | true | 5 | 0 | FAIL | W-STUDENT |
| W1213 | 1000 | 5000 | true | 6 | 0 | FAIL | W-STUDENT |
| W1214 | 1000 | 5000 | true | 7 | 1.000 | FAIL | W-STUDENT |
| W1215 | 1000 | 5000 | true | 8 | REJECT | FAIL | W-INVALID |
| W1216 | 1000 | 5000 | false | 0 | REJECT | FAIL | W-INVALID |
| W1217 | 1000 | 5000 | false | 1 | 0 | FAIL | W-HIGH |
| W1218 | 1000 | 5000 | false | 2 | 0 | FAIL | W-HIGH |
| W1219 | 1000 | 5000 | false | 3 | 0 | FAIL | W-HIGH |
| W1220 | 1000 | 5000 | false | 4 | 0 | FAIL | W-HIGH |
| W1221 | 1000 | 5000 | false | 5 | 0 | FAIL | W-HIGH |
| W1222 | 1000 | 5000 | false | 6 | 0 | FAIL | W-HIGH |
| W1223 | 1000 | 5000 | false | 7 | 0 | FAIL | W-HIGH |
| W1224 | 1000 | 5000 | false | 8 | REJECT | FAIL | W-INVALID |
| W1225 | 1000 | 5000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W1226 | 1000 | 5000.01 | true | 1 | 1.000 | FAIL | W-STUDENT |
| W1227 | 1000 | 5000.01 | true | 2 | 0 | FAIL | W-STUDENT |
| W1228 | 1000 | 5000.01 | true | 3 | 0 | FAIL | W-STUDENT |
| W1229 | 1000 | 5000.01 | true | 4 | 0 | FAIL | W-STUDENT |
| W1230 | 1000 | 5000.01 | true | 5 | 0 | FAIL | W-STUDENT |
| W1231 | 1000 | 5000.01 | true | 6 | 0 | FAIL | W-STUDENT |
| W1232 | 1000 | 5000.01 | true | 7 | 1.000 | FAIL | W-STUDENT |
| W1233 | 1000 | 5000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W1234 | 1000 | 5000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W1235 | 1000 | 5000.01 | false | 1 | 0 | FAIL | W-HIGH |
| W1236 | 1000 | 5000.01 | false | 2 | 0 | FAIL | W-HIGH |
| W1237 | 1000 | 5000.01 | false | 3 | 0 | FAIL | W-HIGH |
| W1238 | 1000 | 5000.01 | false | 4 | 0 | FAIL | W-HIGH |
| W1239 | 1000 | 5000.01 | false | 5 | 0 | FAIL | W-HIGH |
| W1240 | 1000 | 5000.01 | false | 6 | 0 | FAIL | W-HIGH |
| W1241 | 1000 | 5000.01 | false | 7 | 0 | FAIL | W-HIGH |
| W1242 | 1000 | 5000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W1243 | 1000 | 9999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W1244 | 1000 | 9999.99 | true | 1 | 1.000 | FAIL | W-STUDENT |
| W1245 | 1000 | 9999.99 | true | 2 | 0 | FAIL | W-STUDENT |
| W1246 | 1000 | 9999.99 | true | 3 | 0 | FAIL | W-STUDENT |
| W1247 | 1000 | 9999.99 | true | 4 | 0 | FAIL | W-STUDENT |
| W1248 | 1000 | 9999.99 | true | 5 | 0 | FAIL | W-STUDENT |
| W1249 | 1000 | 9999.99 | true | 6 | 0 | FAIL | W-STUDENT |
| W1250 | 1000 | 9999.99 | true | 7 | 1.000 | FAIL | W-STUDENT |
| W1251 | 1000 | 9999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W1252 | 1000 | 9999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W1253 | 1000 | 9999.99 | false | 1 | 0 | FAIL | W-HIGH |
| W1254 | 1000 | 9999.99 | false | 2 | 0 | FAIL | W-HIGH |
| W1255 | 1000 | 9999.99 | false | 3 | 0 | FAIL | W-HIGH |
| W1256 | 1000 | 9999.99 | false | 4 | 0 | FAIL | W-HIGH |
| W1257 | 1000 | 9999.99 | false | 5 | 0 | FAIL | W-HIGH |
| W1258 | 1000 | 9999.99 | false | 6 | 0 | FAIL | W-HIGH |
| W1259 | 1000 | 9999.99 | false | 7 | 0 | FAIL | W-HIGH |
| W1260 | 1000 | 9999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W1261 | 1000 | 10000 | true | 0 | REJECT | FAIL | W-INVALID |
| W1262 | 1000 | 10000 | true | 1 | 1.000 | FAIL | W-STUDENT |
| W1263 | 1000 | 10000 | true | 2 | 0 | FAIL | W-STUDENT |
| W1264 | 1000 | 10000 | true | 3 | 0 | FAIL | W-STUDENT |
| W1265 | 1000 | 10000 | true | 4 | 0 | FAIL | W-STUDENT |
| W1266 | 1000 | 10000 | true | 5 | 0 | FAIL | W-STUDENT |
| W1267 | 1000 | 10000 | true | 6 | 0 | FAIL | W-STUDENT |
| W1268 | 1000 | 10000 | true | 7 | 1.000 | FAIL | W-STUDENT |
| W1269 | 1000 | 10000 | true | 8 | REJECT | FAIL | W-INVALID |
| W1270 | 1000 | 10000 | false | 0 | REJECT | FAIL | W-INVALID |
| W1271 | 1000 | 10000 | false | 1 | 0 | PASS | — |
| W1272 | 1000 | 10000 | false | 2 | 0 | PASS | — |
| W1273 | 1000 | 10000 | false | 3 | 0 | PASS | — |
| W1274 | 1000 | 10000 | false | 4 | 0 | PASS | — |
| W1275 | 1000 | 10000 | false | 5 | 0 | PASS | — |
| W1276 | 1000 | 10000 | false | 6 | 0 | PASS | — |
| W1277 | 1000 | 10000 | false | 7 | 0 | PASS | — |
| W1278 | 1000 | 10000 | false | 8 | REJECT | FAIL | W-INVALID |
| W1279 | 1000 | 10000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W1280 | 1000 | 10000.01 | true | 1 | 1.000 | FAIL | W-STUDENT |
| W1281 | 1000 | 10000.01 | true | 2 | 0 | FAIL | W-STUDENT |
| W1282 | 1000 | 10000.01 | true | 3 | 0 | FAIL | W-STUDENT |
| W1283 | 1000 | 10000.01 | true | 4 | 0 | FAIL | W-STUDENT |
| W1284 | 1000 | 10000.01 | true | 5 | 0 | FAIL | W-STUDENT |
| W1285 | 1000 | 10000.01 | true | 6 | 0 | FAIL | W-STUDENT |
| W1286 | 1000 | 10000.01 | true | 7 | 1.000 | FAIL | W-STUDENT |
| W1287 | 1000 | 10000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W1288 | 1000 | 10000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W1289 | 1000 | 10000.01 | false | 1 | 0 | PASS | — |
| W1290 | 1000 | 10000.01 | false | 2 | 0 | PASS | — |
| W1291 | 1000 | 10000.01 | false | 3 | 0 | PASS | — |
| W1292 | 1000 | 10000.01 | false | 4 | 0 | PASS | — |
| W1293 | 1000 | 10000.01 | false | 5 | 0 | PASS | — |
| W1294 | 1000 | 10000.01 | false | 6 | 0 | PASS | — |
| W1295 | 1000 | 10000.01 | false | 7 | 0 | PASS | — |
| W1296 | 1000 | 10000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W1297 | 1000.01 | -0.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W1298 | 1000.01 | -0.01 | true | 1 | REJECT | FAIL | W-INVALID |
| W1299 | 1000.01 | -0.01 | true | 2 | REJECT | FAIL | W-INVALID |
| W1300 | 1000.01 | -0.01 | true | 3 | REJECT | FAIL | W-INVALID |
| W1301 | 1000.01 | -0.01 | true | 4 | REJECT | FAIL | W-INVALID |
| W1302 | 1000.01 | -0.01 | true | 5 | REJECT | FAIL | W-INVALID |
| W1303 | 1000.01 | -0.01 | true | 6 | REJECT | FAIL | W-INVALID |
| W1304 | 1000.01 | -0.01 | true | 7 | REJECT | FAIL | W-INVALID |
| W1305 | 1000.01 | -0.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W1306 | 1000.01 | -0.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W1307 | 1000.01 | -0.01 | false | 1 | REJECT | FAIL | W-INVALID |
| W1308 | 1000.01 | -0.01 | false | 2 | REJECT | FAIL | W-INVALID |
| W1309 | 1000.01 | -0.01 | false | 3 | REJECT | FAIL | W-INVALID |
| W1310 | 1000.01 | -0.01 | false | 4 | REJECT | FAIL | W-INVALID |
| W1311 | 1000.01 | -0.01 | false | 5 | REJECT | FAIL | W-INVALID |
| W1312 | 1000.01 | -0.01 | false | 6 | REJECT | FAIL | W-INVALID |
| W1313 | 1000.01 | -0.01 | false | 7 | REJECT | FAIL | W-INVALID |
| W1314 | 1000.01 | -0.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W1315 | 1000.01 | 0 | true | 0 | REJECT | FAIL | W-INVALID |
| W1316 | 1000.01 | 0 | true | 1 | 1.00001 | FAIL | W-STUDENT |
| W1317 | 1000.01 | 0 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W1318 | 1000.01 | 0 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W1319 | 1000.01 | 0 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W1320 | 1000.01 | 0 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W1321 | 1000.01 | 0 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W1322 | 1000.01 | 0 | true | 7 | 1.00001 | FAIL | W-STUDENT |
| W1323 | 1000.01 | 0 | true | 8 | REJECT | FAIL | W-INVALID |
| W1324 | 1000.01 | 0 | false | 0 | REJECT | FAIL | W-INVALID |
| W1325 | 1000.01 | 0 | false | 1 | 3.00003 | FAIL | W-LOW |
| W1326 | 1000.01 | 0 | false | 2 | 3.00003 | FAIL | W-LOW |
| W1327 | 1000.01 | 0 | false | 3 | 3.00003 | FAIL | W-LOW |
| W1328 | 1000.01 | 0 | false | 4 | 3.00003 | FAIL | W-LOW |
| W1329 | 1000.01 | 0 | false | 5 | 3.00003 | FAIL | W-LOW |
| W1330 | 1000.01 | 0 | false | 6 | 3.00003 | FAIL | W-LOW |
| W1331 | 1000.01 | 0 | false | 7 | 3.00003 | FAIL | W-LOW |
| W1332 | 1000.01 | 0 | false | 8 | REJECT | FAIL | W-INVALID |
| W1333 | 1000.01 | 0.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W1334 | 1000.01 | 0.01 | true | 1 | 1.00001 | FAIL | W-STUDENT |
| W1335 | 1000.01 | 0.01 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W1336 | 1000.01 | 0.01 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W1337 | 1000.01 | 0.01 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W1338 | 1000.01 | 0.01 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W1339 | 1000.01 | 0.01 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W1340 | 1000.01 | 0.01 | true | 7 | 1.00001 | FAIL | W-STUDENT |
| W1341 | 1000.01 | 0.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W1342 | 1000.01 | 0.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W1343 | 1000.01 | 0.01 | false | 1 | 3.00003 | FAIL | W-LOW |
| W1344 | 1000.01 | 0.01 | false | 2 | 3.00003 | FAIL | W-LOW |
| W1345 | 1000.01 | 0.01 | false | 3 | 3.00003 | FAIL | W-LOW |
| W1346 | 1000.01 | 0.01 | false | 4 | 3.00003 | FAIL | W-LOW |
| W1347 | 1000.01 | 0.01 | false | 5 | 3.00003 | FAIL | W-LOW |
| W1348 | 1000.01 | 0.01 | false | 6 | 3.00003 | FAIL | W-LOW |
| W1349 | 1000.01 | 0.01 | false | 7 | 3.00003 | FAIL | W-LOW |
| W1350 | 1000.01 | 0.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W1351 | 1000.01 | 999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W1352 | 1000.01 | 999.99 | true | 1 | 1.00001 | FAIL | W-STUDENT |
| W1353 | 1000.01 | 999.99 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W1354 | 1000.01 | 999.99 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W1355 | 1000.01 | 999.99 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W1356 | 1000.01 | 999.99 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W1357 | 1000.01 | 999.99 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W1358 | 1000.01 | 999.99 | true | 7 | 1.00001 | FAIL | W-STUDENT |
| W1359 | 1000.01 | 999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W1360 | 1000.01 | 999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W1361 | 1000.01 | 999.99 | false | 1 | 3.00003 | FAIL | W-LOW |
| W1362 | 1000.01 | 999.99 | false | 2 | 3.00003 | FAIL | W-LOW |
| W1363 | 1000.01 | 999.99 | false | 3 | 3.00003 | FAIL | W-LOW |
| W1364 | 1000.01 | 999.99 | false | 4 | 3.00003 | FAIL | W-LOW |
| W1365 | 1000.01 | 999.99 | false | 5 | 3.00003 | FAIL | W-LOW |
| W1366 | 1000.01 | 999.99 | false | 6 | 3.00003 | FAIL | W-LOW |
| W1367 | 1000.01 | 999.99 | false | 7 | 3.00003 | FAIL | W-LOW |
| W1368 | 1000.01 | 999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W1369 | 1000.01 | 1000 | true | 0 | REJECT | FAIL | W-INVALID |
| W1370 | 1000.01 | 1000 | true | 1 | 1.00001 | FAIL | W-STUDENT |
| W1371 | 1000.01 | 1000 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W1372 | 1000.01 | 1000 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W1373 | 1000.01 | 1000 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W1374 | 1000.01 | 1000 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W1375 | 1000.01 | 1000 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W1376 | 1000.01 | 1000 | true | 7 | 1.00001 | FAIL | W-STUDENT |
| W1377 | 1000.01 | 1000 | true | 8 | REJECT | FAIL | W-INVALID |
| W1378 | 1000.01 | 1000 | false | 0 | REJECT | FAIL | W-INVALID |
| W1379 | 1000.01 | 1000 | false | 1 | 1.00001 | PASS | — |
| W1380 | 1000.01 | 1000 | false | 2 | 1.00001 | PASS | — |
| W1381 | 1000.01 | 1000 | false | 3 | 1.00001 | PASS | — |
| W1382 | 1000.01 | 1000 | false | 4 | 1.00001 | PASS | — |
| W1383 | 1000.01 | 1000 | false | 5 | 1.00001 | PASS | — |
| W1384 | 1000.01 | 1000 | false | 6 | 1.00001 | PASS | — |
| W1385 | 1000.01 | 1000 | false | 7 | 1.00001 | PASS | — |
| W1386 | 1000.01 | 1000 | false | 8 | REJECT | FAIL | W-INVALID |
| W1387 | 1000.01 | 1000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W1388 | 1000.01 | 1000.01 | true | 1 | 1.00001 | FAIL | W-STUDENT |
| W1389 | 1000.01 | 1000.01 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W1390 | 1000.01 | 1000.01 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W1391 | 1000.01 | 1000.01 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W1392 | 1000.01 | 1000.01 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W1393 | 1000.01 | 1000.01 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W1394 | 1000.01 | 1000.01 | true | 7 | 1.00001 | FAIL | W-STUDENT |
| W1395 | 1000.01 | 1000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W1396 | 1000.01 | 1000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W1397 | 1000.01 | 1000.01 | false | 1 | 1.00001 | PASS | — |
| W1398 | 1000.01 | 1000.01 | false | 2 | 1.00001 | PASS | — |
| W1399 | 1000.01 | 1000.01 | false | 3 | 1.00001 | PASS | — |
| W1400 | 1000.01 | 1000.01 | false | 4 | 1.00001 | PASS | — |
| W1401 | 1000.01 | 1000.01 | false | 5 | 1.00001 | PASS | — |
| W1402 | 1000.01 | 1000.01 | false | 6 | 1.00001 | PASS | — |
| W1403 | 1000.01 | 1000.01 | false | 7 | 1.00001 | PASS | — |
| W1404 | 1000.01 | 1000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W1405 | 1000.01 | 4999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W1406 | 1000.01 | 4999.99 | true | 1 | 1.00001 | FAIL | W-STUDENT |
| W1407 | 1000.01 | 4999.99 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W1408 | 1000.01 | 4999.99 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W1409 | 1000.01 | 4999.99 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W1410 | 1000.01 | 4999.99 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W1411 | 1000.01 | 4999.99 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W1412 | 1000.01 | 4999.99 | true | 7 | 1.00001 | FAIL | W-STUDENT |
| W1413 | 1000.01 | 4999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W1414 | 1000.01 | 4999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W1415 | 1000.01 | 4999.99 | false | 1 | 1.00001 | PASS | — |
| W1416 | 1000.01 | 4999.99 | false | 2 | 1.00001 | PASS | — |
| W1417 | 1000.01 | 4999.99 | false | 3 | 1.00001 | PASS | — |
| W1418 | 1000.01 | 4999.99 | false | 4 | 1.00001 | PASS | — |
| W1419 | 1000.01 | 4999.99 | false | 5 | 1.00001 | PASS | — |
| W1420 | 1000.01 | 4999.99 | false | 6 | 1.00001 | PASS | — |
| W1421 | 1000.01 | 4999.99 | false | 7 | 1.00001 | PASS | — |
| W1422 | 1000.01 | 4999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W1423 | 1000.01 | 5000 | true | 0 | REJECT | FAIL | W-INVALID |
| W1424 | 1000.01 | 5000 | true | 1 | 1.00001 | FAIL | W-STUDENT |
| W1425 | 1000.01 | 5000 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W1426 | 1000.01 | 5000 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W1427 | 1000.01 | 5000 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W1428 | 1000.01 | 5000 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W1429 | 1000.01 | 5000 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W1430 | 1000.01 | 5000 | true | 7 | 1.00001 | FAIL | W-STUDENT |
| W1431 | 1000.01 | 5000 | true | 8 | REJECT | FAIL | W-INVALID |
| W1432 | 1000.01 | 5000 | false | 0 | REJECT | FAIL | W-INVALID |
| W1433 | 1000.01 | 5000 | false | 1 | 0.00 | FAIL | W-HIGH |
| W1434 | 1000.01 | 5000 | false | 2 | 0.00 | FAIL | W-HIGH |
| W1435 | 1000.01 | 5000 | false | 3 | 0.00 | FAIL | W-HIGH |
| W1436 | 1000.01 | 5000 | false | 4 | 0.00 | FAIL | W-HIGH |
| W1437 | 1000.01 | 5000 | false | 5 | 0.00 | FAIL | W-HIGH |
| W1438 | 1000.01 | 5000 | false | 6 | 0.00 | FAIL | W-HIGH |
| W1439 | 1000.01 | 5000 | false | 7 | 0.00 | FAIL | W-HIGH |
| W1440 | 1000.01 | 5000 | false | 8 | REJECT | FAIL | W-INVALID |
| W1441 | 1000.01 | 5000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W1442 | 1000.01 | 5000.01 | true | 1 | 1.00001 | FAIL | W-STUDENT |
| W1443 | 1000.01 | 5000.01 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W1444 | 1000.01 | 5000.01 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W1445 | 1000.01 | 5000.01 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W1446 | 1000.01 | 5000.01 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W1447 | 1000.01 | 5000.01 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W1448 | 1000.01 | 5000.01 | true | 7 | 1.00001 | FAIL | W-STUDENT |
| W1449 | 1000.01 | 5000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W1450 | 1000.01 | 5000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W1451 | 1000.01 | 5000.01 | false | 1 | 0.00 | FAIL | W-HIGH |
| W1452 | 1000.01 | 5000.01 | false | 2 | 0.00 | FAIL | W-HIGH |
| W1453 | 1000.01 | 5000.01 | false | 3 | 0.00 | FAIL | W-HIGH |
| W1454 | 1000.01 | 5000.01 | false | 4 | 0.00 | FAIL | W-HIGH |
| W1455 | 1000.01 | 5000.01 | false | 5 | 0.00 | FAIL | W-HIGH |
| W1456 | 1000.01 | 5000.01 | false | 6 | 0.00 | FAIL | W-HIGH |
| W1457 | 1000.01 | 5000.01 | false | 7 | 0.00 | FAIL | W-HIGH |
| W1458 | 1000.01 | 5000.01 | false | 8 | REJECT | FAIL | W-INVALID |
| W1459 | 1000.01 | 9999.99 | true | 0 | REJECT | FAIL | W-INVALID |
| W1460 | 1000.01 | 9999.99 | true | 1 | 1.00001 | FAIL | W-STUDENT |
| W1461 | 1000.01 | 9999.99 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W1462 | 1000.01 | 9999.99 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W1463 | 1000.01 | 9999.99 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W1464 | 1000.01 | 9999.99 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W1465 | 1000.01 | 9999.99 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W1466 | 1000.01 | 9999.99 | true | 7 | 1.00001 | FAIL | W-STUDENT |
| W1467 | 1000.01 | 9999.99 | true | 8 | REJECT | FAIL | W-INVALID |
| W1468 | 1000.01 | 9999.99 | false | 0 | REJECT | FAIL | W-INVALID |
| W1469 | 1000.01 | 9999.99 | false | 1 | 0.00 | FAIL | W-HIGH |
| W1470 | 1000.01 | 9999.99 | false | 2 | 0.00 | FAIL | W-HIGH |
| W1471 | 1000.01 | 9999.99 | false | 3 | 0.00 | FAIL | W-HIGH |
| W1472 | 1000.01 | 9999.99 | false | 4 | 0.00 | FAIL | W-HIGH |
| W1473 | 1000.01 | 9999.99 | false | 5 | 0.00 | FAIL | W-HIGH |
| W1474 | 1000.01 | 9999.99 | false | 6 | 0.00 | FAIL | W-HIGH |
| W1475 | 1000.01 | 9999.99 | false | 7 | 0.00 | FAIL | W-HIGH |
| W1476 | 1000.01 | 9999.99 | false | 8 | REJECT | FAIL | W-INVALID |
| W1477 | 1000.01 | 10000 | true | 0 | REJECT | FAIL | W-INVALID |
| W1478 | 1000.01 | 10000 | true | 1 | 1.00001 | FAIL | W-STUDENT |
| W1479 | 1000.01 | 10000 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W1480 | 1000.01 | 10000 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W1481 | 1000.01 | 10000 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W1482 | 1000.01 | 10000 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W1483 | 1000.01 | 10000 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W1484 | 1000.01 | 10000 | true | 7 | 1.00001 | FAIL | W-STUDENT |
| W1485 | 1000.01 | 10000 | true | 8 | REJECT | FAIL | W-INVALID |
| W1486 | 1000.01 | 10000 | false | 0 | REJECT | FAIL | W-INVALID |
| W1487 | 1000.01 | 10000 | false | 1 | 0.00 | PASS | — |
| W1488 | 1000.01 | 10000 | false | 2 | 0.00 | PASS | — |
| W1489 | 1000.01 | 10000 | false | 3 | 0.00 | PASS | — |
| W1490 | 1000.01 | 10000 | false | 4 | 0.00 | PASS | — |
| W1491 | 1000.01 | 10000 | false | 5 | 0.00 | PASS | — |
| W1492 | 1000.01 | 10000 | false | 6 | 0.00 | PASS | — |
| W1493 | 1000.01 | 10000 | false | 7 | 0.00 | PASS | — |
| W1494 | 1000.01 | 10000 | false | 8 | REJECT | FAIL | W-INVALID |
| W1495 | 1000.01 | 10000.01 | true | 0 | REJECT | FAIL | W-INVALID |
| W1496 | 1000.01 | 10000.01 | true | 1 | 1.00001 | FAIL | W-STUDENT |
| W1497 | 1000.01 | 10000.01 | true | 2 | 0.00 | FAIL | W-STUDENT |
| W1498 | 1000.01 | 10000.01 | true | 3 | 0.00 | FAIL | W-STUDENT |
| W1499 | 1000.01 | 10000.01 | true | 4 | 0.00 | FAIL | W-STUDENT |
| W1500 | 1000.01 | 10000.01 | true | 5 | 0.00 | FAIL | W-STUDENT |
| W1501 | 1000.01 | 10000.01 | true | 6 | 0.00 | FAIL | W-STUDENT |
| W1502 | 1000.01 | 10000.01 | true | 7 | 1.00001 | FAIL | W-STUDENT |
| W1503 | 1000.01 | 10000.01 | true | 8 | REJECT | FAIL | W-INVALID |
| W1504 | 1000.01 | 10000.01 | false | 0 | REJECT | FAIL | W-INVALID |
| W1505 | 1000.01 | 10000.01 | false | 1 | 0.00 | PASS | — |
| W1506 | 1000.01 | 10000.01 | false | 2 | 0.00 | PASS | — |
| W1507 | 1000.01 | 10000.01 | false | 3 | 0.00 | PASS | — |
| W1508 | 1000.01 | 10000.01 | false | 4 | 0.00 | PASS | — |
| W1509 | 1000.01 | 10000.01 | false | 5 | 0.00 | PASS | — |
| W1510 | 1000.01 | 10000.01 | false | 6 | 0.00 | PASS | — |
| W1511 | 1000.01 | 10000.01 | false | 7 | 0.00 | PASS | — |
| W1512 | 1000.01 | 10000.01 | false | 8 | REJECT | FAIL | W-INVALID |

### Deposit

| id | amount | balance | student | expected | Observed | Fault |
|---|---|---|---|---|---|---|
| D01 | 25 | 250 | true | 0 | FAIL | D-STUDENT-LOW |
| D02 | 25 | 1000 | true | 0 | FAIL | D-STUDENT-LOW |
| D03 | 25 | 6000 | true | 0.125 | PASS | — |
| D04 | 75 | 250 | true | 0.1875 | FAIL | D-STUDENT-HIGH |
| D05 | 75 | 1000 | true | 0.375 | FAIL | D-STUDENT-HIGH |
| D06 | 75 | 6000 | true | 0.375 | PASS | — |
| D07 | 125 | 1000 | false | 0.125 | FAIL | D-NONSTUDENT-LOW |
| D08 | 125 | 5000 | false | 0.125 | FAIL | D-NONSTUDENT-LOW |
| D09 | 125 | 15000 | false | 0 | FAIL | D-NONSTUDENT-LOW |
| D10 | 375 | 1000 | false | 1.500 | FAIL | D-NONSTUDENT-HIGH |
| D11 | 375 | 5000 | false | 3.000 | FAIL | D-NONSTUDENT-HIGH |
| D12 | 375 | 15000 | false | 3.000 | FAIL | D-NONSTUDENT-HIGH |
| D13 | 50 | 500 | true | 0 | FAIL | D-STUDENT-LOW |
| D14 | 50 | 5000 | true | 0 | FAIL | D-STUDENT-LOW |
| D15 | 75 | 500 | true | 0.1875 | FAIL | D-STUDENT-HIGH |
| D16 | 250 | 2500 | false | 0.250 | FAIL | D-NONSTUDENT-LOW |
| D17 | 250 | 10000 | false | 0.250 | FAIL | D-NONSTUDENT-LOW |
| D18 | 375 | 2500 | false | 1.500 | FAIL | D-NONSTUDENT-HIGH |
| D19 | 0 | 0 | true | 0 | PASS | — |
| D20 | 0 | 0 | false | 0.000 | PASS | — |
| D21 | -0.01 | 1000 | true | REJECT | FAIL | D-INVALID |
| D22 | 75 | -0.01 | true | REJECT | FAIL | D-INVALID |
| D23 | -0.01 | 5000 | false | REJECT | FAIL | D-INVALID |
| D24 | 375 | -0.01 | false | REJECT | FAIL | D-INVALID |

### Transfer

| id | amount | from | to | student | rate | expected | Observed | Fault |
|---|---|---|---|---|---|---|---|---|
| T01 | 199 | 1999 | 999 | true | 0.001 | 0.199 | FAIL | T-RULES |
| T02 | 199 | 1999 | 1000 | true | 0.0005 | 0.0995 | FAIL | T-RULES |
| T03 | 199 | 2000 | 999 | true | 0.0005 | 0.0995 | FAIL | T-RULES |
| T04 | 199 | 2000 | 1000 | true | 0.00025 | 0.04975 | FAIL | T-RULES |
| T05 | 200 | 1999 | 999 | true | 0.0005 | 0.1000 | FAIL | T-RULES |
| T06 | 200 | 1999 | 1000 | true | 0.00025 | 0.05000 | FAIL | T-RULES |
| T07 | 200 | 2000 | 999 | true | 0.0025 | 0.5000 | FAIL | T-RULES |
| T08 | 200 | 2000 | 1000 | true | 0.00125 | 0.25000 | FAIL | T-RULES |
| T09 | 99 | 3999 | 1999 | false | 0.002 | 0.198 | FAIL | T-RULES |
| T10 | 99 | 3999 | 2000 | false | 0.001 | 0.099 | FAIL | T-RULES |
| T11 | 99 | 4000 | 1999 | false | 0.01 | 0.99 | FAIL | T-RULES |
| T12 | 99 | 4000 | 2000 | false | 0.005 | 0.495 | FAIL | T-RULES |
| T13 | 100 | 1999 | 999 | false | 0.002 | 0.200 | FAIL | T-RULES |
| T14 | 100 | 1999 | 1000 | false | 0.001 | 0.100 | FAIL | T-RULES |
| T15 | 100 | 2000 | 999 | false | 0.005 | 0.500 | FAIL | T-RULES |
| T16 | 100 | 2000 | 1000 | false | 0.0025 | 0.2500 | FAIL | T-RULES |

## 3. Fault localization

Every failed case is assigned exactly one primary localization below. Some cases may exercise
multiple wrong constants; these are grouped by the affected business-rule branch.

| Fault ID | Failing cases | Suspected fault | Justification |
|---|---|---|---|
| P-LENGTH | 26; e.g. P01, P02, P03 | atm.utils.FormatChecker.checkPinFormat, lines 33–40 | The pin.length == 4 check rejects specified five-digit PINs and accepts a four-digit PIN. |
| S-POSITIVE | 2; e.g. S36, S38 | atm.session.Session.setAmount, lines 87–91; CashValidator.validateWithdrawal, lines 20–31 | There is no positive-amount guard, so zero and negative multiples of 50 pass validation. |
| S-BILLS | 3; e.g. S42, S44, S46 | atm.utils.CashValidator.validateWithdrawal, lines 23–27 | Taking amount % 50 before % 20 rejects valid 60, 80, and 110; e.g. 110 = 50 + 3*20. |
| S-LIMIT | 1; e.g. S49 | atm.session.Session.setAmount, lines 87–96 | There is no daily-limit check or account limit field, so the dispensable $1,020 withdrawal is accepted. |
| W-INVALID | 588; e.g. W0001, W0002, W0003 | bank.utils.FeesCalculator.calculateWithdrawalFee, lines 6–30 | ASSUMPTION-DEPENDENT: no guard rejects negative money/day codes outside 1..7 with IllegalArgumentException. |
| W-STUDENT | 385; e.g. W0452, W0453, W0454 | bank.utils.FeesCalculator.calculateWithdrawalFee, lines 12–15 | The weekend and weekday rates are reversed, charging weekdays and waiving weekend fees. |
| W-LOW | 105; e.g. W0461, W0462, W0463 | bank.utils.FeesCalculator.calculateWithdrawalFee, lines 18–19 | Balances below $1,000 use 0.002 instead of the specified 0.003. |
| W-HIGH | 105; e.g. W0569, W0570, W0571 | bank.utils.FeesCalculator.calculateWithdrawalFee, lines 20–21 | The middle tier extends to $10,000 instead of $5,000 and therefore charges a specified free withdrawal. |
| D-STUDENT-LOW | 4; e.g. D01, D02, D13 | bank.utils.FeesCalculator.calculateDepositInterest, lines 46–50 | Student deposits <=$50 with balance <=$5,000 receive rate 0.002 instead of zero. |
| D-STUDENT-HIGH | 3; e.g. D04, D05, D15 | bank.utils.FeesCalculator.calculateDepositInterest, lines 39–50 | Student deposits >$50 are split at $100 rather than $50, with further incorrect balance thresholds/rates. |
| D-NONSTUDENT-LOW | 5; e.g. D07, D08, D09 | bank.utils.FeesCalculator.calculateDepositInterest, lines 61–64 | Nonstudent deposits <=$250 use 0.005/0 instead of zero/0.001 above/at-below $10,000. |
| D-NONSTUDENT-HIGH | 4; e.g. D10, D11, D12 | bank.utils.FeesCalculator.calculateDepositInterest, lines 54–64 | Nonstudent deposits >$250 are split at $500 with a $5,000 balance threshold and wrong rates. |
| D-INVALID | 4; e.g. D21, D22, D23 | bank.utils.FeesCalculator.calculateDepositInterest, lines 33–72 | ASSUMPTION-DEPENDENT: negative amounts/balances are calculated rather than rejected with IllegalArgumentException. |
| T-RULES | 16; e.g. T01, T02, T03 | bank.utils.FeesCalculator.calculateTransferFee, lines 80–149 | Every decision-table row disagrees: student amount split is $100 instead of $200, source/destination splits and fractional rates are also incorrect (e.g. T01 uses 0.025 instead of 0.001). |

The per-case mapping above and the full observed assertion messages in
[assignment1-results.csv](assignment1-results.csv) give the exhaustive failure list.

FormatChecker also excludes digit 9 via `pin[i] >= '9'` (line 35). Valid five-digit cases
containing 9 currently fail at the length check first, so the digit defect is masked and
is not claimed as an independently isolated failure. Fixes belong in the later fix phase.
