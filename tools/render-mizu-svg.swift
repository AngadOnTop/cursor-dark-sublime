#!/usr/bin/env swift
import AppKit
import Foundation

let arguments = CommandLine.arguments
guard arguments.count > 1, (arguments.count - 1).isMultiple(of: 3) else {
    fputs("usage: render-mizu-svg.swift SVG SIZE OUTPUT [SVG SIZE OUTPUT ...]\n", stderr)
    exit(2)
}

for index in stride(from: 1, to: arguments.count, by: 3) {
    let input = arguments[index]
    guard let size = Int(arguments[index + 1]), size > 0 else {
        fputs("invalid icon size: \(arguments[index + 1])\n", stderr)
        exit(2)
    }
    let output = arguments[index + 2]

    guard let image = NSImage(contentsOfFile: input),
          let bitmap = NSBitmapImageRep(
              bitmapDataPlanes: nil,
              pixelsWide: size,
              pixelsHigh: size,
              bitsPerSample: 8,
              samplesPerPixel: 4,
              hasAlpha: true,
              isPlanar: false,
              colorSpaceName: .deviceRGB,
              bytesPerRow: 0,
              bitsPerPixel: 0
          ) else {
        fputs("could not load SVG: \(input)\n", stderr)
        exit(1)
    }

    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: bitmap)
    NSColor.clear.setFill()
    NSRect(x: 0, y: 0, width: size, height: size).fill()
    let padding = max(1, size / 16)
    image.draw(
        in: NSRect(
            x: padding,
            y: padding,
            width: size - (padding * 2),
            height: size - (padding * 2)
        ),
        from: .zero,
        operation: .sourceOver,
        fraction: 1
    )
    NSGraphicsContext.restoreGraphicsState()

    guard let png = bitmap.representation(using: .png, properties: [:]) else {
        fputs("could not encode PNG: \(output)\n", stderr)
        exit(1)
    }
    do {
        try png.write(to: URL(fileURLWithPath: output))
    } catch {
        fputs("could not write PNG: \(output): \(error)\n", stderr)
        exit(1)
    }
}
