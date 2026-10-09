# Experimental 16-bit PQ TIFF ICC

The 16-bit path now uses the source-matched linear matrix ICC as the basis for a sampled PQ EOTF tone-curve profile. The RGB colorant and white-point tags are retained. PQ values are scaled with the user-provided reference white (default is not inferred). The ICC TRC is normalized to PQ's 10,000-nit range.

**Important:** This is a provisional matrix/TRC representation, not a verified HDR interchange profile. ICC relative colorimetry does not by itself signal absolute HDR luminance or guarantee Photoshop's HDR display mode. The 16-bit TIFF may display differently from the source. Do not publish this feature as production-ready before a Photoshop comparison, ICC validation by ColorSync, and reference-white evaluation.

Check TIFF tag 34675 and orientation 274 using ExifTool, then open in Photoshop and inspect its assigned profile and HDR rendering.
