import Foundation
import CoreGraphics
import CoreImage
import ImageIO

func fail(_ message: String) -> Never {
    fputs("Error: \(message)\n", stderr)
    exit(1)
}

let args = CommandLine.arguments
guard args.count == 4, let count = Int(args[3]), (1...64).contains(count) else {
    fail("Usage: hdr_probe inspect-hdr SOURCE.HEIC SAMPLES(1..64)")
}
let url = URL(fileURLWithPath: args[2])
guard let source = CGImageSourceCreateWithURL(url as CFURL, nil) else {
    fail("Cannot open source")
}
guard CGImageSourceCopyAuxiliaryDataInfoAtIndex(
    source, 0, kCGImageAuxiliaryDataTypeHDRGainMap
) != nil else { fail("No Apple HDR gain map found") }

guard let linearP3 = CGColorSpace(name: CGColorSpace.extendedLinearDisplayP3) else {
    fail("Extended linear Display P3 unavailable")
}
let context = CIContext(options: [
    .workingColorSpace: linearP3,
    .outputColorSpace: linearP3,
    .useSoftwareRenderer: false
])

struct Result {
    let report: [String: Any]
    let sampleValues: [Float]
}

func measure(_ hdr: Bool) -> Result {
    // ImageIO requires the decode *request* key, with HDR/SDR as its value.
    // Using kCGImageSourceDecodeToHDR as the dictionary key silently ignored
    // the request and produced identical results in both branches.
    let decodeMode = hdr ? kCGImageSourceDecodeToHDR : kCGImageSourceDecodeToSDR
    let options: [CFString: Any] = [kCGImageSourceDecodeRequest: decodeMode]
    guard let decoded = CGImageSourceCreateImageAtIndex(source, 0, options as CFDictionary) else {
        fail("ImageIO decode failed (HDR=\(hdr))")
    }
    let width = decoded.width
    let height = decoded.height
    let ci = CIImage(cgImage: decoded)
    let rowBytes = width * 4 * MemoryLayout<Float>.size
    var pixels = [Float](repeating: 0, count: width * height * 4)
    pixels.withUnsafeMutableBytes { bytes in
        guard let address = bytes.baseAddress else { fail("No bitmap storage") }
        context.render(
            ci,
            toBitmap: address,
            rowBytes: rowBytes,
            bounds: CGRect(x: 0, y: 0, width: width, height: height),
            format: .RGBAf,
            colorSpace: linearP3
        )
    }
    var minima = [Double](repeating: .infinity, count: 3)
    var maxima = [Double](repeating: -.infinity, count: 3)
    var aboveOne = 0
    var sampled = 0
    var invalid = 0
    let stridePixels = max(1, width * height / 100_000)
    for i in Swift.stride(from: 0, to: width * height, by: stridePixels) {
        let offset = i * 4
        let rgb = (0..<3).map { Double(pixels[offset + $0]) }
        if !rgb.allSatisfy({ $0.isFinite }) { invalid += 1; continue }
        for c in 0..<3 {
            minima[c] = min(minima[c], rgb[c])
            maxima[c] = max(maxima[c], rgb[c])
        }
        if rgb.contains(where: { $0 > 1 }) { aboveOne += 1 }
        sampled += 1
    }
    var points: [[String: Any]] = []
    var sampleValues: [Float] = []
    for i in 0..<count {
        let x = (2 * i + 1) * width / (2 * count)
        let y = height / 2
        let offset = (y * width + x) * 4
        let rgb = (0..<3).map { pixels[offset + $0] }
        sampleValues.append(contentsOf: rgb)
        points.append(["x": x, "y_raw": y, "rgb_linear_p3": rgb.map(Double.init)])
    }
    let report: [String: Any] = [
        "decoded_bits_per_component": decoded.bitsPerComponent,
        "rendered_format": "RGBAf_float32",
        "min_rgb": sampled > 0 ? minima : [0, 0, 0],
        "max_rgb": sampled > 0 ? maxima : [0, 0, 0],
        "pixels_above_one": aboveOne,
        "sampled_pixels": sampled,
        "invalid_pixels": invalid,
        "samples": points
    ]
    return Result(report: report, sampleValues: sampleValues)
}

let sdr = measure(false)
let hdr = measure(true)
let maxSampleDifference = zip(sdr.sampleValues, hdr.sampleValues)
    .map { abs(Double($0) - Double($1)) }.max() ?? 0
let output: [String: Any] = [
    "source": url.lastPathComponent,
    "working_space": "extendedLinearDisplayP3",
    "decode_option": "kCGImageSourceDecodeRequest",
    "sdr": sdr.report,
    "hdr": hdr.report,
    "max_sample_difference": maxSampleDifference,
    "hdr_decode_distinct_at_sample_points": maxSampleDifference > 1e-6,
    "note": "Explicit SDR/HDR ImageIO decode requests; compare measured values before accepting reconstruction."
]
guard JSONSerialization.isValidJSONObject(output),
      let data = try? JSONSerialization.data(withJSONObject: output, options: [.sortedKeys]),
      let json = String(data: data, encoding: .utf8) else {
    fail("JSON serialization failed")
}
print(json)
