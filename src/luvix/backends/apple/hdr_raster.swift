import Foundation
import CoreGraphics
import CoreImage
import ImageIO

func fail(_ message: String) -> Never {
    fputs("Error: \(message)\n", stderr)
    exit(1)
}

// Write raw interleaved Float32 RGBA in native little-endian order and a JSON sidecar.
// Raw pixel orientation is retained. Source HEIC is never modified.
let args = CommandLine.arguments
guard args.count == 3 else { fail("Usage: hdr_raster SOURCE.HEIC OUTPUT_PREFIX") }
let sourceURL = URL(fileURLWithPath: args[1])
let prefix = URL(fileURLWithPath: args[2])
guard !FileManager.default.fileExists(atPath: prefix.path + ".rgba32f"),
      !FileManager.default.fileExists(atPath: prefix.path + ".json") else {
    fail("Refusing to overwrite existing intermediate")
}
guard let source = CGImageSourceCreateWithURL(sourceURL as CFURL, nil) else {
    fail("Cannot open source")
}
guard CGImageSourceCopyAuxiliaryDataInfoAtIndex(
    source, 0, kCGImageAuxiliaryDataTypeHDRGainMap
) != nil else { fail("No Apple HDR gain map found") }
let options: [CFString: Any] = [kCGImageSourceDecodeRequest: kCGImageSourceDecodeToHDR]
guard let decoded = CGImageSourceCreateImageAtIndex(source, 0, options as CFDictionary) else {
    fail("HDR decode failed")
}
// Only use a linear working space with the same primaries as the input.
// Reject unsupported profiles rather than silently converting to Display P3.
let baseOptions: [CFString: Any] = [kCGImageSourceDecodeRequest: kCGImageSourceDecodeToSDR]
guard let base = CGImageSourceCreateImageAtIndex(source, 0, baseOptions as CFDictionary),
      let sourceSpace = base.colorSpace else { fail("Cannot determine source color space") }
let sourceName = (sourceSpace.name as String?) ?? ""
let linearName: CFString
let sourcePrimaries: String
if sourceName == (CGColorSpace.displayP3 as String) {
    linearName = CGColorSpace.extendedLinearDisplayP3
    sourcePrimaries = "Display P3"
} else if sourceName == (CGColorSpace.sRGB as String) {
    linearName = CGColorSpace.extendedLinearSRGB
    sourcePrimaries = "sRGB"
} else {
    fail("Unsupported source color space: \(sourceName). No implicit gamut conversion permitted")
}
guard let linearP3 = CGColorSpace(name: linearName) else {
    fail("Requested linear working color space unavailable")
}
let width = decoded.width
let height = decoded.height
let rowBytes = width * 4 * MemoryLayout<Float>.size
let context = CIContext(options: [
    .workingColorSpace: linearP3,
    .outputColorSpace: linearP3
])
let image = CIImage(cgImage: decoded)
var pixels = [Float](repeating: 0, count: width * height * 4)
pixels.withUnsafeMutableBytes { bytes in
    guard let address = bytes.baseAddress else { fail("Allocation failed") }
    context.render(
        image, toBitmap: address, rowBytes: rowBytes,
        bounds: CGRect(x: 0, y: 0, width: width, height: height),
        format: .RGBAf, colorSpace: linearP3
    )
}
let finite = pixels.allSatisfy { $0.isFinite }
guard finite else { fail("Non-finite HDR pixel detected") }
let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil)
    as? [String: Any]

let orientation = properties?[kCGImagePropertyOrientation as String]
    as? Int ?? 1
let rawURL = URL(fileURLWithPath: prefix.path + ".rgba32f")
let jsonURL = URL(fileURLWithPath: prefix.path + ".json")
let payload: [String: Any] = [
    "width": width, "height": height, "channels": 4,
    "dtype": "<f4", "layout": "RGBA", "orientation": orientation,
    "color_space": sourcePrimaries == "Display P3" ? "extendedLinearDisplayP3" : "extendedLinearSRGB",
    "source_primaries": sourcePrimaries,
    "decode_request": "kCGImageSourceDecodeToHDR",
    "reference_white": "relative SDR white = 1.0",
    "source": sourceURL.lastPathComponent
]
guard let metadata = try? JSONSerialization.data(withJSONObject: payload, options: [.sortedKeys]) else {
    fail("JSON encoding failed")
}
do {
    try FileManager.default.createDirectory(at: prefix.deletingLastPathComponent(), withIntermediateDirectories: true)
    let rawData = pixels.withUnsafeBytes { Data($0) }
    try rawData.write(to: rawURL, options: .atomic)
    try metadata.write(to: jsonURL, options: .atomic)
    print(String(data: metadata, encoding: .utf8) ?? "{}")
} catch {
    try? FileManager.default.removeItem(at: rawURL)
    try? FileManager.default.removeItem(at: jsonURL)
    fail("Writing HDR intermediate failed: \(error)")
}
