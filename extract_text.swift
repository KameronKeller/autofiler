import Foundation
import Vision
import PDFKit
import AppKit

func extractTextFromPDF(at filePath: String) -> String {
    let pdfURL = URL(fileURLWithPath: filePath)
    guard let pdfDocument = PDFDocument(url: pdfURL) else {
        print("Could not load PDF document")
        return ""
    }

    let pageCount = pdfDocument.pageCount
    var allText = ""

    for pageIndex in 0..<pageCount {
        guard let page = pdfDocument.page(at: pageIndex),
              let pageImage = pageToImage(page: page, resolution: 300), // Increase resolution
              let cgPageImage = pageImage.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
            continue
        }

        let requestHandler = VNImageRequestHandler(cgImage: cgPageImage, options: [:])
        let recognizeTextRequest = VNRecognizeTextRequest { (request, error) in
            if let error = error {
                print("Error recognizing text: \(error.localizedDescription)")
                return
            }
            guard let observations = request.results as? [VNRecognizedTextObservation] else {
                return
            }

            for observation in observations {
                if let topCandidate = observation.topCandidates(1).first {
                    allText += topCandidate.string + " "
                }
            }
        }
        recognizeTextRequest.recognitionLevel = .accurate // Set recognition level to accurate
        recognizeTextRequest.usesLanguageCorrection = true // Enable language correction

        do {
            try requestHandler.perform([recognizeTextRequest])
        } catch {
            print("Failed to perform vision request: \(error.localizedDescription)")
        }
    }

    return allText
}

func pageToImage(page: PDFPage, resolution: CGFloat) -> NSImage? {
    let pageRect = page.bounds(for: .mediaBox)
    let scale = resolution / 72.0 // Default PDF resolution is 72 DPI
    let scaledSize = NSSize(width: pageRect.width * scale, height: pageRect.height * scale)
    let img = NSImage(size: scaledSize)
    img.lockFocus()
    NSColor.white.set()
    pageRect.fill()
    if let context = NSGraphicsContext.current?.cgContext {
        context.scaleBy(x: scale, y: scale)
        page.draw(with: .mediaBox, to: context)
    }
    img.unlockFocus()
    return img
}

// Usage
if CommandLine.arguments.count < 2 {
    print("Please provide a file path")
} else {
    let filePath = CommandLine.arguments[1]
    let extractedText = extractTextFromPDF(at: filePath)
    print(extractedText)
}