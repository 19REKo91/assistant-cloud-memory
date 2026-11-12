# Partial triangle geometry implementation — 2026-11-12

## Current implementation
The interactive workbench now contains one calculated Euclidean triangle, for lithium (Li, Z=3). The original 118 mass-map points, polyline, axes, and plotted positions remain unchanged.

The workbench also now has:
- Zoom controls, wheel zoom, and drag-to-pan wired to the actual SVG element.
- A display-scale slider. This changes only the visual size of the overlaid geometry; it is not a physical conversion between AB units and the mass-map axes.
- A separate SVG triangle overlay layer.

## Lithium calculation (direct table values)
Input angles, preserved as supplied:
- θ₁ = 84.05°
- θ₂ = 46.95°
- θ₃ = 49.00°
- Sum = 180.00°

Using AB = c = 3:
- a = BC = 3 sin(84.05°) / sin(49°) = 3.9536243915
- b = CA = 3 sin(46.95°) / sin(49°) = 2.9047925978
- A = (0, 0)
- B = (3, 0)
- C = (b cos(84.05°), b sin(84.05°)) = (0.3011123678, 2.8891437102)

Incenter (weighted by opposite side lengths):
- G = (0.9755841031, 0.8791909634)

The SVG overlay translates G to the original Li plot point (122.1367521368, 268.705). The triangle is rendered around that point using the visual-only slider scale.

## Hydrogen diagnostic — deliberately not drawn as a triangle
The documented hydrogen test gives:
- θ₁ = 85.84°
- θ₂ raw = 70,227°
- derived periodic θ₂ used in that test = 27°
- θ₃ = 7°

These three test angles sum to 119.84°, not 180°. Therefore, regardless of the documented side-length calculation, they do not satisfy the Euclidean interior-angle condition used for the triangle construction above. Hydrogen is not drawn as a Euclidean triangle in this workbench. Its raw and derived values are not silently altered.

## Data limitation
The complete θ₁, θ₂, θ₃, n, S_C, B, d(C), status table sent in the conversation is not present as a verbatim data file in the repository, and the available conversation retrieval did not recover its full rows. The old elements_118.csv is not substituted. Only values explicitly available in the current working record are used.

Consequently:
- This is a partial geometry implementation, not a completed 118-triangle overlay.
- No triangle is invented for the remaining elements.
- The three anomalous negative-θ₂ cases and seven excluded cases are not forced into Euclidean triangles.
- Other non-180° angle sums require the user's established geometric interpretation before any construction is attempted.

## Verification snapshot
After the latest update, the HTML was fetched back from GitHub and checked:
- SVG chart element has the chart ID required by the controls.
- 118 original circle plot points remain.
- Exactly one geometry record is present (Li).
- The H triangle record is absent.
- The triangle overlay layer and display-scale slider are present.

Page path: PROJECTS/element-mass-doubling/element-mass-triangle-overlay-workbench.html

## Follow-up implementation — classification and export
The chart now draws colored rings around the unchanged original blue points for the 3 Anomalous (Be, B, C), 11 Gas (H, He, N, O, F, Ne, Cl, Ar, Kr, Xe, Rn), and 7 Excluded (Db, Sg, Bh, Hs, Mt, Ds, Rg) elements. Each ring has a hover title with Z, symbol, and status. The classification marker is a separate SVG layer; it does not move or replace the original points.

An Export SVG button serializes the current SVG chart, including the classification and triangle layers, to an SVG file. This is a browser-side export feature.
