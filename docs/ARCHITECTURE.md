# Architecture and interoperability

Gaincraft aims to be a format-aware Swiss Army knife for HDR gain-map images. Separate capture backends from gain-map representation, color management, raster export, and CLI.

```text
Apple HEIC + auxiliary gain map
  |-- inspect / extract -> base.png + gainmap.png + manifest.json
  |-- rebuild <- edited components + original HEIC metadata
  `-- ImageIO HDR decode -> extended linear float RGB
                             |-- float32 linear TIFF + matching ICC
                             `-- uint16 PQ TIFF + reference-white nits + PQ ICC
```

The native macOS backend uses explicit ImageIO HDR decode requests. A source profile cannot be copied blindly to a TIFF with a different transfer function. `--color-space source` means preserve primaries/white point *when supported*, using the destination's linear or PQ transfer. Current tested spaces: Display P3 and sRGB; additional ICC spaces require tests. A supplied external P3 PQ ICC is presently necessary for the known-good 16-bit Photoshop workflow.

HEIC component extraction retains raw raster alignment. TIFFs preserve the original orientation tag. Gain-map metadata and encoding differ across standards. Apple auxiliary HEIC/JPEG, ISO 21496-1, and Ultra HDR JPEG/MPF/XMP must be detected and validated separately. Future multi-channel color gain maps require a richer intermediate than Apple's monochrome L008.

Validation has three layers: (1) structure/metadata/ICC/orientation, (2) numerical HDR and inverse-PQ fidelity, and (3) actual HDR appearance in Photoshop and independent viewers. The private Trinity fixture and GPS metadata must never enter public CI artifacts.
