import Foundation
import CoreGraphics

func fail(_ message: String) -> Never {
    fputs("Error: \(message)\n", stderr)
    exit(1)
}

guard (2...3).contains(CommandLine.arguments.count) else {
    fail("Usage: icc_profile OUTPUT.icc")
}
let profileName = CommandLine.arguments.count == 3 ? CommandLine.arguments[2] : "p3"
let spaceName: CFString = profileName == "srgb"
    ? CGColorSpace.extendedLinearSRGB : CGColorSpace.extendedLinearDisplayP3
guard let space = CGColorSpace(name: spaceName) else {
    fail("Extended linear Display P3 is unavailable")
}
guard let profile = space.copyICCData() else {
    fail("No ICC profile data available for extended linear Display P3")
}
let data = profile as Data
guard data.count >= 128 else { fail("ICC data is unexpectedly short") }
let declaredSize = data.prefix(4).reduce(UInt32(0)) { ($0 << 8) | UInt32($1) }
guard declaredSize == data.count else { fail("ICC header length mismatch") }
guard data.subdata(in: 36..<40) == Data("acsp".utf8) else {
    fail("ICC signature missing")
}
let output = URL(fileURLWithPath: CommandLine.arguments[1])
do { try data.write(to: output, options: .atomic) }
catch { fail("Cannot write ICC profile: \(error)") }
print("Exported extended linear Display P3 ICC (\(data.count) bytes)")
