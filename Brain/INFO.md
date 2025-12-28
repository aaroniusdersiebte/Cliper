Lass uns den ansatz nochmal komplett überdenken.
Leider klappt das mit dem markieren und ausrechnen nicht wirklich gut. (komische berechnung des timecodes...)

ich habe es aber gerade geschafft mit diesem obs raw send und einem Plugin folgendes zu erschaffen, damit sollten wir das ganze doch lösen können oder



{
  "requestType": "CallVendorRequest",
  "requestData": {
    "vendorName": "streamup-chapter-manager",
    "requestType": "setAnnotation",
    "requestData": {
	    "annotationText": "%user%",
	    "annotationSource": "fe"
    }
  }
}



ergebniss: eine txt xml oder edl datei, zb 2025-12-27 00-30-53_chapters.txt

Chapter Markers for 2025-12-27 00-30-53
00:00:00 - Start
00:00:04 - (Annotation) aaron (fe)
00:00:11 - End


(natürlich ist der inhalt noch anpassbar)