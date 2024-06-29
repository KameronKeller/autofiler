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
    var allText = "" // Variable to accumulate all recognized text

    for pageIndex in 0..<pageCount {
        guard let page = pdfDocument.page(at: pageIndex),
              let pageImage = pageToImage(page: page),
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
                    allText += topCandidate.string + " " // Append recognized text
                }
            }
        }

        do {
            try requestHandler.perform([recognizeTextRequest])
        } catch {
            print("Failed to perform vision request: \(error.localizedDescription)")
        }
    }

    return allText
}

func pageToImage(page: PDFPage) -> NSImage? {
    let pageRect = page.bounds(for: .mediaBox)
    let img = NSImage(size: pageRect.size)
    img.lockFocus()
    NSColor.white.set()
    pageRect.fill()
    page.draw(with: .mediaBox, to: NSGraphicsContext.current!.cgContext)
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