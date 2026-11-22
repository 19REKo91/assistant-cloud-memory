# New angle-map candidate — independent mathematical test
Date: 2026-11-22
Status: unapproved experimental candidate; no element values have been transformed.

## 1. Scope
This candidate is designed from scratch for the 118-element rebalance experiment. It does not use any angle, boundary, constant, reference element, or rule from prior framework versions. It is a mathematical construction proposal only.

## 2. Two independent input coordinates
For an element with valid atomic mass M and density rho, define the elemental molar volume:
V_atom = M_atomic / rho
where M_atomic is in g mol^-1 and rho is in g cm^-3. The result is cm^3 per mole of atoms.

The inputs M, rho, and V_atom are not three independent variables because V_atom is derived from M and rho. The angle map therefore uses two independent coordinates:
- x: normalized density coordinate
- y: normalized elemental molar-volume coordinate

Candidate normalization methods to compare:
A. empirical percentile ranks of log(rho) and log(V_atom);
B. robust log scaling using median and median absolute deviation, then a bounded transform to [0,1];
C. min-max scaling only as a sensitivity comparison, not as the default, because extrema can dominate.

The reference population used to calculate x and y must be specified before the actual element calculation. Phase/source cohort choices remain unresolved in the cohort map.

## 3. Positive-angle transformation candidate
For x,y in [0,1], define:
u = 2x - 1
v = 2y - 1

For a sensitivity parameter lambda > 0:
w_A = exp(lambda*u)
w_B = exp(lambda*v)
w_C = exp(-lambda*(u+v))

Then:
A = 180*w_A/(w_A+w_B+w_C)
B = 180*w_B/(w_A+w_B+w_C)
C = 180*w_C/(w_A+w_B+w_C)

Mathematical guarantees:
- all weights are strictly positive for finite x,y,lambda;
- all three angles are strictly positive;
- A+B+C = 180 degrees by construction;
- A and B respond symmetrically to the two normalized inputs;
- C is a mathematical balancing component, not a third measured physical property.

## 4. Sensitivity sweep over the complete normalized square
A deterministic grid test was run over x,y in [0,1], using 201 points per axis (40,401 input pairs per lambda). It tested only the mathematical mapping, not the 118 element data.

| lambda | Minimum angle observed | Maximum angle observed | Maximum sum error |
|---:|---:|---:|---:|
| 0.25 | 34.3905° | 92.5577° | 5.7e-14° |
| 0.50 | 18.0662° | 124.4589° | 5.7e-14° |
| 1.00 | 4.3720° | 163.6997° | 5.7e-14° |
| 2.00 | 0.2228° | 179.1121° | 5.7e-14° |

Interpretation: lambda controls triangle extremity strongly. lambda=2 produces near-degenerate shapes; lambda=1 can produce very acute angles; lambda=0.25 and 0.50 are less extreme on the normalized square. No lambda is selected or approved.

## 5. Candidate triangle construction and incenter
For each angle triple (A,B,C), choose a display scale with side c=1 opposite angle C:
a = sin(A)/sin(C)
b = sin(B)/sin(C)

Using vertices:
P_A=(0,0), P_B=(1,0), P_C=(b*cos(A), b*sin(A))

The incenter candidate is the side-length-weighted vertex average:
I = (a*P_A + b*P_B + c*P_C)/(a+b+c)

This point is the intersection of the three internal angle bisectors. It is a candidate for the plotted point only; the point definition still needs to be fixed for the experiment.

## 6. Failure and edge-case rules
- If mass or density is missing, invalid, or unresolved, do not fabricate x or y.
- If the chosen reference cohort has no valid spread for a property, the normalization is undefined and the element is flagged.
- Do not clip invalid values silently.
- Use stable numerical evaluation for exponentials.
- Keep the original source values and all derived fields in separate columns.
- The visual should distinguish measured/primary, secondary, predicted, and unavailable values.

## 7. Decision still required by evidence, not preference
Before applying this candidate to the 118 elements, the data audit must decide:
1. Which density cohort(s) are physically comparable.
2. Which normalization method defines x and y.
3. Whether one common lambda or a documented sensitivity panel is more informative.
4. Whether the incenter is the final plotted point.

No element triangles, element angle rows, or unified image have been generated from this candidate.
