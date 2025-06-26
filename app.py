import platform
platform.mac_ver = lambda: ('14.5.0', ('', '', ''), '')

from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import os
import uuid
from music21 import stream, note, chord, midi, scale, instrument, converter, environment
from pydub import AudioSegment

app = Flask(__name__)
CORS(app)

OUTPUT_DIR = 'generated'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Update LilyPond path if required
us = environment.UserSettings()
# Uncomment and update the path if needed
# us['lilypondPath'] = '/path/to/lilypond'  # e.g., 'C:/Program Files (x86)/LilyPond/usr/bin/lilypond.exe'

def generate_midi(payload):
    s = stream.Stream()
    s.append(instrument.Piano())

    scale_type = payload['scale_type']
    root = payload['root_note']
    min_pitch = payload['min_pitch']
    max_pitch = payload['max_pitch']
    duration = payload['duration']
    tempo = payload['tempo']
    rhythm_choices = payload['rhythm_choices']
    use_arpeggios = payload['use_arpeggios']
    arp_prob = payload['arpeggio_probability']
    smoothness = payload['melody_smoothness_bias']

    for _ in range(int(duration)):
        pitch = random.randint(min_pitch, max_pitch)
        dur = random.choice(rhythm_choices)
        s.append(note.Note(pitch, quarterLength=dur))

    midi_file = f"{uuid.uuid4().hex}.mid"
    midi_path = os.path.join(OUTPUT_DIR, midi_file)
    s.write('midi', fp=midi_path)
    return midi_file

def convert_midi_to_pdf(midi_path, pdf_path):
    try:
        score = converter.parse(midi_path)
        # Export using LilyPond as a PDF
        score.write('lily.pdf', fp=pdf_path)
    except Exception as e:
        print(f"[ERROR] Could not generate PDF from MIDI: {e}")
        # Fallback to a placeholder PDF
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(pdf_path)
        c.drawString(100, 750, "Generated Music Sheet")
        c.drawString(100, 730, f"MIDI File: {os.path.basename(midi_path)}")
        c.drawString(100, 710, "Note info (could not parse MIDI)")
        c.save()

def convert_midi_to_wav(midi_path, wav_path):
    try:
        sound = AudioSegment.from_file(midi_path, format="mid")
        sound.export(wav_path, format="wav")
    except Exception as e:
        print(f"Error converting MIDI to WAV: {e}")
        AudioSegment.silent(duration=1000).export(wav_path, format="wav")

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/generate', methods=['POST'])
def generate():
    payload = request.get_json()
    midi_file = generate_midi(payload)

    midi_path = os.path.join(OUTPUT_DIR, midi_file)
    wav_file = midi_file.replace('.mid', '.wav')
    pdf_file = midi_file.replace('.mid', '.pdf')

    convert_midi_to_wav(midi_path, os.path.join(OUTPUT_DIR, wav_file))
    convert_midi_to_pdf(midi_path, os.path.join(OUTPUT_DIR, pdf_file))

    return jsonify({
        "midi_file": midi_file,
        "wav_file": wav_file,
        "pdf_file": pdf_file
    })

@app.route('/music/<filename>')
def serve_music(filename):
    return send_from_directory(OUTPUT_DIR, filename)

@app.route('/sheet/<filename>')
def serve_sheet(filename):
    return send_from_directory(OUTPUT_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
