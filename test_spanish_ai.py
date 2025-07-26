#!/usr/bin/env python3

import asyncio
import json
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent))

from app.services.unified_ai_service import UnifiedAIService
from app.core.config import settings

async def test_spanish_content_generation():
    """Test Spanish educational content generation"""
    print("🚀 Prueba de Generación de Contenido Educativo en Español")
    print("=" * 60)
    
    # Load Spanish sample text
    sample_file = Path("sample_documents/fundamentos_aprendizaje_automatico.txt")
    if not sample_file.exists():
        print("❌ No se encontró el documento de muestra en español")
        return
    
    with open(sample_file, 'r', encoding='utf-8') as f:
        sample_text = f.read()[:1500]  # Limit for testing
    
    print(f"📖 Texto de muestra cargado: {len(sample_text)} caracteres")
    print()
    
    try:
        # Initialize AI service
        ai_service = UnifiedAIService()
        
        # Get service status
        status = ai_service.get_service_status()
        print("🔧 Estado de los servicios de IA:")
        print(f"  Claude disponible: {status['claude_available']}")
        print(f"  OpenAI disponible: {status['openai_available']}")
        print(f"  Servicio primario: {status['primary_service']}")
        print(f"  Idioma por defecto: {status['default_language']}")
        print()
        
        # Test flashcards in Spanish
        print("🔄 Generando tarjetas de estudio en español...")
        try:
            flashcards = await ai_service.generate_flashcards(sample_text, count=3, language="es")
            print(f"✅ Generadas {len(flashcards)} tarjetas de estudio")
            
            for i, card in enumerate(flashcards, 1):
                print(f"  Tarjeta {i}:")
                print(f"    Pregunta: {card.question}")
                print(f"    Respuesta: {card.answer}")
                print(f"    Dificultad: {card.difficulty}")
                print()
        except Exception as e:
            print(f"❌ Error generando tarjetas: {str(e)}")
        
        # Test multiple choice in Spanish
        print("🔄 Generando preguntas de opción múltiple en español...")
        try:
            questions = await ai_service.generate_multiple_choice(sample_text, count=2, language="es")
            print(f"✅ Generadas {len(questions)} preguntas de opción múltiple")
            
            for i, q in enumerate(questions, 1):
                print(f"  Pregunta {i}: {q.question}")
                for j, option in enumerate(q.options):
                    marker = "✓" if j == q.correct_answer else " "
                    print(f"    {marker} {chr(65+j)}. {option}")
                if q.explanation:
                    print(f"    Explicación: {q.explanation}")
                print()
        except Exception as e:
            print(f"❌ Error generando opción múltiple: {str(e)}")
        
        # Test true/false in Spanish
        print("🔄 Generando preguntas verdadero/falso en español...")
        try:
            tf_questions = await ai_service.generate_true_false(sample_text, count=2, language="es")
            print(f"✅ Generadas {len(tf_questions)} preguntas verdadero/falso")
            
            for i, q in enumerate(tf_questions, 1):
                print(f"  Pregunta {i}: {q.statement}")
                print(f"    Respuesta: {'Verdadero' if q.correct_answer else 'Falso'}")
                if q.explanation:
                    print(f"    Explicación: {q.explanation}")
                print()
        except Exception as e:
            print(f"❌ Error generando verdadero/falso: {str(e)}")
        
        # Test summary in Spanish
        print("🔄 Generando resumen en español...")
        try:
            summaries = await ai_service.generate_summary(sample_text, language="es")
            print(f"✅ Generado resumen")
            
            if summaries:
                summary = summaries[0]
                print(f"  Título: {summary.title}")
                print(f"  Contenido: {summary.content[:200]}...")
                print(f"  Puntos clave:")
                for point in summary.key_points:
                    print(f"    • {point}")
                print()
        except Exception as e:
            print(f"❌ Error generando resumen: {str(e)}")
        
    except Exception as e:
        print(f"❌ Error inicializando servicio de IA: {str(e)}")
        print("💡 Asegúrate de configurar ANTHROPIC_API_KEY o OPENAI_API_KEY en tu archivo .env")

async def test_english_fallback():
    """Test English content generation as fallback"""
    print("\n🔄 Probando generación en inglés como respaldo...")
    
    sample_text = """
    Machine Learning is a subset of artificial intelligence that focuses on developing 
    algorithms that can learn and make decisions from data. It includes supervised 
    learning, unsupervised learning, and reinforcement learning approaches.
    """
    
    try:
        ai_service = UnifiedAIService()
        
        flashcards = await ai_service.generate_flashcards(sample_text, count=2, language="en")
        print(f"✅ Generadas {len(flashcards)} tarjetas en inglés")
        
        if flashcards:
            print(f"  Ejemplo: {flashcards[0].question}")
            print(f"  Respuesta: {flashcards[0].answer}")
        
    except Exception as e:
        print(f"❌ Error generando contenido en inglés: {str(e)}")

async def main():
    """Run all tests"""
    print("🎯 Suite de Pruebas - Studium Backend con Claude Sonnet 4")
    print("=" * 60)
    
    # Test Spanish content generation
    await test_spanish_content_generation()
    
    # Test English fallback
    await test_english_fallback()
    
    print("=" * 60)
    print("🎉 ¡Suite de pruebas completada!")
    print()
    print("📝 Próximos pasos:")
    print("1. Configura tu ANTHROPIC_API_KEY en el archivo .env")
    print("2. Ejecuta: python main.py")
    print("3. Visita: http://localhost:8000/docs")
    print("4. Prueba el endpoint: http://localhost:8000/api/v1/ai-status")

if __name__ == "__main__":
    asyncio.run(main())