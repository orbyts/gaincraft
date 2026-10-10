import Foundation
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

func die(_ message: String) -> Never { fputs("Error: \(message)\n", stderr); exit(1) }
func source(_ url: URL) -> CGImageSource {
    guard let s = CGImageSourceCreateWithURL(url as CFURL, nil) else { die("Cannot open \(url.path)") }
    return s
}
func auxiliary(_ s: CGImageSource) -> [String: Any] {
    guard let d = CGImageSourceCopyAuxiliaryDataInfoAtIndex(s, 0, kCGImageAuxiliaryDataTypeHDRGainMap) as? [String: Any] else { die("Missing HDR gain map") }
    return d
}
struct MapInfo { let width: Int; let height: Int; let stride: Int; let bytes: Data }
func mapInfo(_ aux: [String: Any]) -> MapInfo {
    guard let desc = aux[kCGImageAuxiliaryDataInfoDataDescription as String] as? [String: Any],
          let w = desc["Width"] as? Int, let h = desc["Height"] as? Int,
          let stride = desc["BytesPerRow"] as? Int,
          let format = desc["PixelFormat"] as? Int,
          let bytes = aux[kCGImageAuxiliaryDataInfoData as String] as? Data,
          format == 1278226488, w > 0, h > 0, stride >= w, bytes.count == stride*h else {
        die("Expected Apple L008 grayscale gain map; unsupported layout")
    }
    return MapInfo(width: w, height: h, stride: stride, bytes: bytes)
}
func grayImage(_ m: MapInfo) -> CGImage {
    guard let provider = CGDataProvider(data: m.bytes as CFData),
          let img = CGImage(width: m.width, height: m.height, bitsPerComponent: 8,
                            bitsPerPixel: 8, bytesPerRow: m.stride,
                            space: CGColorSpaceCreateDeviceGray(),
                            bitmapInfo: CGBitmapInfo(rawValue: 0), provider: provider,
                            decode: nil, shouldInterpolate: false, intent: .defaultIntent) else { die("Could not decode gain map") }
    return img
}
func writePNG(_ image: CGImage, _ url: URL) {
    guard let d = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else { die("Cannot create PNG") }
    CGImageDestinationAddImage(d, image, nil)
    guard CGImageDestinationFinalize(d) else { die("Could not write PNG") }
}
func readEditedMap(_ url: URL, original: MapInfo) -> Data {
    let s = source(url)
    guard let image = CGImageSourceCreateImageAtIndex(s, 0, nil), image.width == original.width, image.height == original.height else { die("Edited map must have dimensions \(original.width)x\(original.height)") }
    // Render as 8-bit DeviceGray; preserve original row padding in output buffer.
    var bytes = [UInt8](original.bytes)
    let success = bytes.withUnsafeMutableBytes { buffer -> Bool in
        guard let ctx = CGContext(data: buffer.baseAddress, width: original.width,
                                  height: original.height, bitsPerComponent: 8,
                                  bytesPerRow: original.stride,
                                  space: CGColorSpaceCreateDeviceGray(),
                                  bitmapInfo: CGImageAlphaInfo.none.rawValue) else { return false }
        ctx.interpolationQuality = .none
        ctx.draw(image, in: CGRect(x: 0, y: 0, width: original.width, height: original.height))
        return true
    }
    guard success else { die("Failed rendering edited gain map") }
    return Data(bytes)
}
func writeHEIC(_ base: CGImage, _ original: CGImageSource, _ aux: [String: Any], _ url: URL) {
    guard let d = CGImageDestinationCreateWithURL(url as CFURL, UTType.heic.identifier as CFString, 1, nil) else { die("Cannot create HEIC") }
    let props = CGImageSourceCopyPropertiesAtIndex(original, 0, nil)
    CGImageDestinationAddImage(d, base, props)
    CGImageDestinationAddAuxiliaryDataInfo(d, kCGImageAuxiliaryDataTypeHDRGainMap, aux as CFDictionary)
    guard CGImageDestinationFinalize(d) else { die("Could not finalize HEIC") }
    let check = source(url)
    _ = mapInfo(auxiliary(check))
    // ImageIO can mark output files hidden; explicitly clear the flag.
    let p = Process(); p.executableURL = URL(fileURLWithPath: "/usr/bin/chflags")
    p.arguments = ["nohidden", url.path]
    do { try p.run(); p.waitUntilExit() } catch { die("chflags failed: \(error)") }
    guard p.terminationStatus == 0 else { die("Could not clear hidden flag") }
}

func details(_ s: CGImageSource) -> [String: Any] {
    let image = CGImageSourceCreateImageAtIndex(s, 0, nil)!
    let m = mapInfo(auxiliary(s))
    let props = CGImageSourceCopyPropertiesAtIndex(s, 0, nil) as? [String: Any] ?? [:]
    let meta = auxiliary(s)[kCGImageAuxiliaryDataInfoMetadata as String]
    return ["base_width": image.width, "base_height": image.height,
            "gain_width": m.width, "gain_height": m.height,
            "gain_stride": m.stride, "gain_format": "L008",
            "color_space": image.colorSpace?.name as String? ?? "unknown",
            "orientation": props[kCGImagePropertyOrientation as String] ?? 1,
            "has_gainmap_metadata": meta != nil]
}
func emitJSON(_ d: [String: Any]) {
    guard let data = try? JSONSerialization.data(withJSONObject: d, options: [.sortedKeys]),
          let text = String(data: data, encoding: .utf8) else { die("JSON error") }
    print(text)
}
let args = CommandLine.arguments
if args.count < 2 { die("Usage: apple_backend inspect|extract|rebuild|validate ...") }
switch args[1] {
case "inspect":
    guard args.count == 3 else { die("inspect source.HEIC") }
    emitJSON(details(source(URL(fileURLWithPath: args[2]))))
case "extract":
    guard args.count == 4 else { die("extract source.HEIC directory") }
    let input = URL(fileURLWithPath: args[2]); let s = source(input)
    let dir = URL(fileURLWithPath: args[3], isDirectory: true)
    do { try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true) } catch { die("Cannot create directory") }
    for name in ["base.png", "gainmap.png", "manifest.json"] {
        guard !FileManager.default.fileExists(atPath: dir.appendingPathComponent(name).path) else { die("Refusing to overwrite " + name) }
    }
    let base = CGImageSourceCreateImageAtIndex(s, 0, nil)!
    writePNG(base, dir.appendingPathComponent("base.png"))
    writePNG(grayImage(mapInfo(auxiliary(s))), dir.appendingPathComponent("gainmap.png"))
    var report = details(s)
    report["source_name"] = input.lastPathComponent
    let data = try! JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
    try! data.write(to: dir.appendingPathComponent("manifest.json"))
    print("Extracted base.png, gainmap.png, manifest.json")
case "rebuild":
    guard args.count == 6 else { die("rebuild source.HEIC base.png|- gainmap.png|- output.HEIC") }
    let original = source(URL(fileURLWithPath: args[2]))
    let origBase = CGImageSourceCreateImageAtIndex(original, 0, nil)!
    let base: CGImage
    if args[3] == "-" { base = origBase }
    else {
        let bs = source(URL(fileURLWithPath: args[3]))
        guard let edited = CGImageSourceCreateImageAtIndex(bs, 0, nil) else { die("Invalid edited base") }
        base = edited
    }
    guard base.width == origBase.width, base.height == origBase.height else { die("Base dimensions mismatch") }
    guard base.colorSpace?.name == origBase.colorSpace?.name else { die("Base color profile mismatch") }
    var aux = auxiliary(original)
    if args[4] != "-" {
        aux[kCGImageAuxiliaryDataInfoData as String] = readEditedMap(URL(fileURLWithPath: args[4]), original: mapInfo(aux))
    }
    let output = URL(fileURLWithPath: args[5])
    guard !FileManager.default.fileExists(atPath: output.path) else { die("Refusing to overwrite existing output") }
    writeHEIC(base, original, aux, output)
    print("Rebuilt: \(output.path)")
case "validate":
    guard args.count == 4 else { die("validate source.HEIC output.HEIC") }
    let a = details(source(URL(fileURLWithPath: args[2])))
    let b = details(source(URL(fileURLWithPath: args[3])))
    let keys = ["base_width", "base_height", "gain_width", "gain_height", "gain_format", "color_space", "orientation"]
    let differences = keys.filter { String(describing: a[$0]) != String(describing: b[$0]) }
    emitJSON(["valid": differences.isEmpty, "mismatched_fields": differences])
    if !differences.isEmpty { exit(2) }
default: die("Unknown command")
}
