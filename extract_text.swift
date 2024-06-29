import Foundation
import Vision
import PDFKit
import AppKit

func extractTextFromPDF(at filePath: String) {
    let pdfURL = URL(fileURLWithPath: filePath)
    guard let pdfDocument = PDFDocument(url: pdfURL) else {
        print("Could not load PDF document")
        return
    }

    let pageCount = pdfDocument.pageCount
    let visionRequests = [VNRecognizeTextRequest(completionHandler: recognizeTextHandler)]

    for pageIndex in 0..<pageCount {
        guard let page = pdfDocument.page(at: pageIndex),
              let pageImage = pageToImage(page: page),
              let cgPageImage = pageImage.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
            continue
        }

        let requestHandler = VNImageRequestHandler(cgImage: cgPageImage, options: [:])
        do {
            try requestHandler.perform(visionRequests)
        } catch {
            print("Failed to perform vision request: \(error.localizedDescription)")
        }
    }
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

func recognizeTextHandler(request: VNRequest, error: Error?) {
    if let error = error {
        print("Error recognizing text: \(error.localizedDescription)")
        return
    }
    guard let observations = request.results as? [VNRecognizedTextObservation] else {
        return
    }

    for observation in observations {
        if let topCandidate = observation.topCandidates(1).first {
            print("Recognized text: \(topCandidate.string)")
        }
    }
}

// Call the function
let filePath = CommandLine.arguments[1]
extractTextFromPDF(at: filePath)