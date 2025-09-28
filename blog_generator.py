"""
EVIKA Blog Generator for AEO and GEO content
Generates structured blog posts with JSON-LD schema markup
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

class BlogGenerator:
    def __init__(self):
        self.language = "en"
        self.brand_name = ""
        self.target_keyword = ""
        self.mode = "AEO"  # AEO or GEO
        
    def generate_blog_post(self, 
                          brand_name: str, 
                          target_keyword: str, 
                          language: str = "en",
                          mode: str = "AEO",
                          context: Dict[str, Any] = None,
                          site_city: str = None) -> Dict[str, Any]:
        """
        Generate a blog post based on the provided parameters
        
        Args:
            brand_name: Name of the brand
            target_keyword: Target keyword for SEO
            language: Language code (default: en)
            mode: AEO or GEO mode
            context: Additional context data from audit
            
        Returns:
            Dict containing the complete blog post with schema markup
        """
        
        self.language = language
        self.brand_name = brand_name
        self.target_keyword = target_keyword
        self.mode = mode.upper()
        self.site_city = site_city
        
        # Generate content based on mode
        if self.mode == "AEO":
            return self._generate_aeo_content(context)
        elif self.mode == "GEO":
            return self._generate_geo_content(context)
        else:
            raise ValueError("Mode must be 'AEO' or 'GEO'")
    
    def _generate_aeo_content(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate AEO-optimized content"""
        
        # AEO-specific content structure
        title = f"{self.target_keyword}: Complete Guide | {self.brand_name}"
        if self.language.startswith('lt'):
            meta_description = f"{self.brand_name} - Išsamus {self.target_keyword} vadovas. Ekspertų patarimai, palyginimai ir patarimai. Pradėkite dabar!"
        else:
            meta_description = f"{self.brand_name} - Complete {self.target_keyword} guide. Expert insights, comparisons & tips. Start now!"
        
        # Generate sections
        sections = self._generate_aeo_sections()
        
        # Generate FAQs (≥5 items)
        faqs = self._generate_aeo_faqs()
        
        # Generate images
        images = self._generate_images()
        
        # Generate internal links
        internal_links = self._generate_internal_links()
        
        # Generate content (800-1200 words)
        content = self._generate_aeo_content_text(sections, faqs)
        
        # Generate JSON-LD schemas
        json_ld = self._generate_aeo_json_ld(faqs)
        
        return {
            "title": title,
            "meta_description": meta_description[:160],
            "content": content,
            "word_count": len(content.split()),
            "sections": sections,
            "faqs": faqs,
            "images": images,
            "internal_links": internal_links,
            "json_ld": json_ld,
            "mode": "AEO",
            "target_keyword": self.target_keyword,
            "brand": self.brand_name,
            "language": self.language,
            "generated_at": datetime.now().isoformat()
        }
    
    def _generate_geo_content(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate GEO-optimized content"""
        
        # GEO-specific content structure
        title = f"{self.target_keyword} in {self._get_city_name()}: Local Guide | {self.brand_name}"
        if self.language.startswith('lt'):
            meta_description = f"{self.brand_name} - Geriausi {self.target_keyword} {self._get_city_name()}. Ekspertų vietinis vadovavimas ir patarimai. Apsilankykite šiandien!"
        else:
            meta_description = f"{self.brand_name} - Best {self.target_keyword} in {self._get_city_name()}. Expert local guidance & insights. Visit us today!"
        
        # Generate sections
        sections = self._generate_geo_sections()
        
        # Generate FAQs (≥5 items)
        faqs = self._generate_geo_faqs()
        
        # Generate images
        images = self._generate_images()
        
        # Generate internal links
        internal_links = self._generate_internal_links()
        
        # Generate content (1000-1400 words)
        content = self._generate_geo_content_text(sections, faqs)
        
        # Generate JSON-LD schemas
        json_ld = self._generate_geo_json_ld(faqs, context)
        
        return {
            "title": title,
            "meta_description": meta_description[:160],
            "content": content,
            "word_count": len(content.split()),
            "sections": sections,
            "faqs": faqs,
            "images": images,
            "internal_links": internal_links,
            "json_ld": json_ld,
            "mode": "GEO",
            "target_keyword": self.target_keyword,
            "brand": self.brand_name,
            "language": self.language,
            "city": self._get_city_name(),
            "generated_at": datetime.now().isoformat()
        }
    
    def _generate_aeo_sections(self) -> List[Dict[str, str]]:
        """Generate AEO-optimized sections with expanded content in target language"""
        if self.language.startswith('lt'):
            return [
                {
                    "heading": f"Kas yra {self.target_keyword}?",
                    "content": f"Suprasti {self.target_keyword} yra labai svarbu priimant pagrįstus sprendimus. {self.brand_name} teikia išsamius patarimus šia tema. Šis vadovas apima viską, ką reikia žinoti apie geriausių variantų paiešką, kainų palyginimą ir protingus sprendimus."
                },
                {
                    "heading": f"{self.target_keyword} pagrindiniai privalumai",
                    "content": f"Atraskite {self.target_keyword} privalumus ir kaip jie gali jums padėti. Mūsų {self.brand_name} ekspertai nustatė svarbiausius privalumus, įskaitant kokybę, patogumą ir vertę. Išsamiai aptarsime kiekvieną privalumą su tikrais pavyzdžiais ir palyginimais."
                },
                {
                    "heading": f"Palyginimas: {self.target_keyword} vs alternatyvos",
                    "content": f"Palyginkite {self.target_keyword} su kitais variantais, kad priimtumėte geriausią sprendimą. {self.brand_name} siūlo išsamius palyginimus, kurie padės jums apsispręsti. Apsvarstysime kainų skirtumus, kokybės variacijas ir prieinamumą skirtinguose variantuose."
                },
                {
                    "heading": f"Kaip pasirinkti tinkamą {self.target_keyword}",
                    "content": f"Išmokite kriterijus, kaip pasirinkti geriausią {self.target_keyword} jūsų poreikiams. {self.brand_name} teikia ekspertų vadovavimą, atsižvelgdama į biudžetą, kokybę ir asmeninius pageidavimus. Pateiksime žingsnis po žingsnio vadovą, kuris padės priimti teisingą sprendimą."
                },
                {
                    "heading": f"Patarimai ir rekomendacijos",
                    "content": f"Gaukite ekspertų patarimų ir rekomendacijų apie {self.target_keyword}. {self.brand_name} dalijasi vidinėmis žiniomis apie tai, ko ieškoti, kokių klaidų vengti ir kaip gauti geriausią vertę už savo pinigus."
                },
                {
                    "heading": f"Išvados: {self.target_keyword} vadovas",
                    "content": f"Priimkite pagrįstus sprendimus apie {self.target_keyword} su mūsų išsamiais vadovais. {self.brand_name} yra jūsų patikimas šaltinis ekspertų patarimams ir profesionaliam vadovavimui."
                }
            ]
        else:  # English fallback
            return [
                {
                    "heading": f"What is {self.target_keyword}?",
                    "content": f"Understanding {self.target_keyword} is essential for making informed decisions. {self.brand_name} provides comprehensive insights into this topic. This guide covers everything you need to know about finding the best options, comparing prices, and making smart choices."
                },
                {
                    "heading": f"Key Benefits of {self.target_keyword}",
                    "content": f"Discover the advantages of {self.target_keyword} and how it can benefit you. Our experts at {self.brand_name} have identified the most important benefits including quality, convenience, and value. We'll explore each benefit in detail with real examples and comparisons."
                },
                {
                    "heading": f"Comparison: {self.target_keyword} vs Alternatives",
                    "content": f"Compare {self.target_keyword} with other options to make the best choice. {self.brand_name} offers detailed comparisons to help you decide. We'll look at price differences, quality variations, and availability across different options."
                },
                {
                    "heading": f"How to Choose the Right {self.target_keyword}",
                    "content": f"Learn the criteria for selecting the best {self.target_keyword} for your needs. {self.brand_name} provides expert guidance on factors like budget, quality, and personal preferences. We'll provide a step-by-step guide to help you make the right decision."
                },
                {
                    "heading": f"Tips and Recommendations",
                    "content": f"Get expert tips and recommendations for {self.target_keyword}. {self.brand_name} shares insider knowledge about what to look for, common mistakes to avoid, and how to get the best value for your money."
                },
                {
                    "heading": f"Conclusion: {self.target_keyword} Guide",
                    "content": f"Make informed decisions about {self.target_keyword} with our comprehensive guide. {self.brand_name} is your trusted source for expert insights and professional recommendations."
                }
            ]
    
    def _generate_geo_sections(self) -> List[Dict[str, str]]:
        """Generate GEO-optimized sections with local references in target language"""
        city = self._get_city_name()
        landmarks = self._get_landmarks()
        if self.language.startswith('lt'):
            return [
                {
                    "heading": f"{self.target_keyword} {city}: Vietinis apžvalga",
                    "content": f"Atraskite geriausias {self.target_keyword} galimybes {city}. {self.brand_name} teikia vietinius patarimus ir rekomendacijas {city} gyventojams. Nuo {landmarks}, mes jums padėsime per geriausias vietas ir kas daro kiekvieną sritį unikalią apsipirkimui."
                },
                {
                    "heading": f"Geriausios {self.target_keyword} vietos {city}",
                    "content": f"Raskite populiariausias {self.target_keyword} vietas {city}, įskaitant sritis šalia {landmarks}. {self.brand_name} geriau žino {city} ir gali rekomenduoti geriausias vietas pagal jūsų pageidavimus. Apžvelgsime prekybos centrus, vietines parduotuves ir paslėptas perlas."
                },
                {
                    "heading": f"Interneto vs vietinis {self.target_keyword} {city}",
                    "content": f"Palyginkite internetinius ir vietinius {self.target_keyword} patirtis {city}. {self.brand_name} padeda pasirinkti geriausią variantą jūsų poreikiams. Aptarsime vietinio apsipirkimo {city} privalumus lyginant su internetiniais variantais, įskaitant nedelsiant prieinamumą, asmeninį aptarnavimą ir vietinę ekspertizę."
                },
                {
                    "heading": f"Vietinio {self.target_keyword} privalumai {city}",
                    "content": f"Išmokite, kodėl vietinis {self.target_keyword} {city} siūlo unikalius privalumus. {self.brand_name} jungia jus su geriausiais vietiniais variantais ir paaiškina vietinių verslų {city} palaikymo privalumus. Apžvelgsime patogumą, vietines žinias ir bendruomenės palaikymą."
                },
                {
                    "heading": f"Geriausi apsipirkimo laikai {city}",
                    "content": f"Atraskite optimalius laikus apsilankyti {self.target_keyword} vietose {city}. {self.brand_name} dalijasi vidiniais patarimais apie tai, kada parduotuvės mažiau apkrautos, kada paprastai vyksta nuolaidos ir kaip suplanuoti apsipirkimo kelionę geriausiai."
                },
                {
                    "heading": f"Išvados: {self.target_keyword} {city}",
                    "content": f"Išnaudokite {self.target_keyword} {city} su mūsų vietiniu vadovu. {self.brand_name} yra jūsų patikimas partneris {city} ir esame įsipareigoję padėti rasti tiksliai tai, ko ieškote."
                }
            ]
        else:  # English fallback
            return [
                {
                    "heading": f"{self.target_keyword} in {city}: Local Overview",
                    "content": f"Discover the best {self.target_keyword} options in {city}. {self.brand_name} provides local insights and recommendations for {city} residents. From {landmarks}, we'll guide you through the top locations and what makes each area unique for shopping."
                },
                {
                    "heading": f"Top {self.target_keyword} Locations in {city}",
                    "content": f"Find the most popular {self.target_keyword} spots in {city}, including areas near {landmarks}. {self.brand_name} knows {city} best and can recommend the best places based on your preferences. We'll cover shopping centers, local boutiques, and hidden gems."
                },
                {
                    "heading": f"Online vs Local {self.target_keyword} in {city}",
                    "content": f"Compare online and local {self.target_keyword} experiences in {city}. {self.brand_name} helps you choose the best option for your needs. We'll discuss the advantages of shopping locally in {city} versus online options, including immediate availability, personal service, and local expertise."
                },
                {
                    "heading": f"Local {self.target_keyword} Benefits in {city}",
                    "content": f"Learn why local {self.target_keyword} in {city} offers unique advantages. {self.brand_name} connects you with the best local options and explains the benefits of supporting local businesses in {city}. We'll cover convenience, local knowledge, and community support."
                },
                {
                    "heading": f"Best Times to Shop in {city}",
                    "content": f"Discover the optimal times to visit {self.target_keyword} locations in {city}. {self.brand_name} shares insider tips about when stores are less crowded, when sales typically occur, and how to plan your shopping trip for the best experience."
                },
                {
                    "heading": f"Conclusion: {self.target_keyword} in {city}",
                    "content": f"Make the most of {self.target_keyword} in {city} with our local guide. {self.brand_name} is your trusted partner in {city} and we're committed to helping you find exactly what you're looking for."
                }
            ]
    
    def _generate_aeo_faqs(self) -> List[Dict[str, str]]:
        """Generate AEO-optimized FAQs based on real user intent with Lithuanian People Also Ask style"""
        if self.language.startswith('lt'):
            return [
                {
                    "question": f"Kur pigiausia pirkti kvepalus Vilniuje?",
                    "answer": f"Geriausios kainos kvepalams Vilniuje randamos {self.brand_name} parduotuvėse. Mes siūlome konkurencingas kainas su skaidriais įkainiais. Turime variantų kiekvienam biudžetui - nuo prieinamų iki premium pasirinkimų."
                },
                {
                    "question": f"Ar galima nusipirkti kvepalų testerius?",
                    "answer": f"Taip! {self.brand_name} siūlo kvepalų testerių galimybes, kad galėtumėte išbandyti prieš pirkdami. Suprantame, kaip svarbu rasti tinkamą variantą, ir mūsų ekspertai padės jums per visą procesą."
                },
                {
                    "question": f"Kur gauti nišinius kvepalus Vilniuje?",
                    "answer": f"{self.brand_name} specializuojasi tiek populiarių, tiek nišinių kvepalų srityje. Turime prieigą prie ekskluzyvių kolekcijų ir galime padėti rasti unikalius kvepalus, kurių nėra kitur. Mūsų ekspertai puikiai žino rinką."
                },
                {
                    "question": f"Ar visi kvepalai autentiški?",
                    "answer": f"Taip, {self.brand_name} garantuoja visų mūsų produktų autentiškumą. Dirbame tiesiogiai su patikrintais tiekėjais ir teikiame autentiškumo sertifikatus. Mūsų reputacija remiasi pasitikėjimu ir kokybės užtikrinimu."
                },
                {
                    "question": f"Kur geriausia kvepalų pasirinkimas Vilniuje?",
                    "answer": f"Geriausias kvepalų pasirinkimas Vilniuje yra {self.brand_name} parduotuvėse. Siūlome platų asortimentą, tinkantį skirtingiems biudžetams ir skoniams, su ekspertų vadovavimu, kuris padės jums pasirinkti."
                },
                {
                    "question": f"Kada geriausia laikas pirkti kvepalus?",
                    "answer": f"Geriausias laikas pirkti kvepalus yra per {self.brand_name} akcijas ir specialius pasiūlymus. Reguliariai organizuojame nuolaidas ir sezoninius pasiūlymus, kurie puikiai tinka Vilniaus pirkėjams."
                }
            ]
        else:  # English fallback
            return [
                {
                    "question": f"What are the best options for {self.target_keyword}?",
                    "answer": f"When looking for the best options, {self.brand_name} recommends considering quality, price, and availability. We offer a wide range of options to suit different budgets and preferences, with expert guidance to help you choose."
                },
                {
                    "question": f"How much should I expect to pay?",
                    "answer": f"Prices vary depending on quality and brand. {self.brand_name} offers competitive pricing with transparent quotes. We have options for every budget, from affordable choices to premium selections, ensuring you get the best value."
                },
                {
                    "question": f"Are there any authentic options available?",
                    "answer": f"Yes, {self.brand_name} guarantees authenticity for all our products. We work directly with verified suppliers and provide certificates of authenticity. Our reputation is built on trust and quality assurance."
                },
                {
                    "question": f"Can I test before buying?",
                    "answer": f"Absolutely! {self.brand_name} offers testing opportunities so you can try before you buy. We understand the importance of finding the right fit, and our experts are available to guide you through the testing process."
                },
                {
                    "question": f"What about niche or specialty options?",
                    "answer": f"{self.brand_name} specializes in both popular and niche options. We have access to exclusive collections and can help you find unique items that aren't available elsewhere. Our experts know the market inside and out."
                },
                {
                    "question": f"Where can I find the cheapest options?",
                    "answer": f"For budget-conscious shoppers, {self.brand_name} offers several affordable options without compromising quality. We regularly have sales and special offers, and our team can help you find the best deals available."
                }
            ]
    
    def _generate_geo_faqs(self) -> List[Dict[str, str]]:
        """Generate GEO-optimized FAQs with local focus in target language"""
        city = self._get_city_name()
        landmarks = self._get_landmarks()
        if self.language.startswith('lt'):
            return [
                {
                    "question": f"Kur galiu rasti geriausius variantus {city}?",
                    "answer": f"{self.brand_name} turi kelias vietas visoje {city}, įskaitant sritis šalia {landmarks}. Galime rekomenduoti geriausias vietas pagal jūsų pageidavimus ir suteikti išsamias instrukcijas į mūsų parduotuves."
                },
                {
                    "question": f"Kokie privalumai apsipirkti vietiniame vs internete?",
                    "answer": f"Apsipirkimas vietiniame {city} su {self.brand_name} siūlo nedelsiant prieinamumą, asmeninį aptarnavimą ir vietinę ekspertizę. Galite pamatyti, paliesti ir išbandyti produktus prieš pirkdami, plius gauti momentinius ekspertų patarimus iš mūsų {city} komandos."
                },
                {
                    "question": f"Ar yra specialių pasiūlymų {city} gyventojams?",
                    "answer": f"Taip, {self.brand_name} siūlo ekskluzyvius pasiūlymus {city} gyventojams, įskaitant vietines nuolaidas ir specialius pasiūlymus. Taip pat turime lojalumo programas ir sezoninius pasiūlymus, kurie puikiai tinka {city} pirkėjams."
                },
                {
                    "question": f"Ar galiu gauti tą pačią dieną paslaugą {city}?",
                    "answer": f"Žinoma! {self.brand_name} teikia tą pačią dieną paslaugas visoje {city}. Mūsų vietinė komanda užtikrina greitą apdorojimą ir dažnai gali prisitaikyti prie skubų {city} klientų prašymų."
                },
                {
                    "question": f"Kuo {self.brand_name} skiriasi nuo kitų variantų {city}?",
                    "answer": f"{self.brand_name} išsiskiria {city} su savo vietine ekspertize, individualizuotu aptarnavimu ir giliu {city} unikalių poreikių supratimu. Mes ne tik dar viena grandinė - mes esame {city} bendruomenės dalis."
                },
                {
                    "question": f"Ar teikiate pristatymą visoje {city}?",
                    "answer": f"Taip, {self.brand_name} teikia išsamias pristatymo paslaugas visoje {city}, įskaitant sritis šalia {landmarks}. Užtikriname greitą, patikimą pristatymą su sekimu ir klientų palaikymu iš mūsų {city} komandos."
                }
            ]
        else:  # English fallback
            return [
                {
                    "question": f"Where can I find the best options in {city}?",
                    "answer": f"{self.brand_name} has multiple locations throughout {city}, including areas near {landmarks}. We can recommend the best spots based on your preferences and provide detailed directions to our stores."
                },
                {
                    "question": f"What are the advantages of shopping locally vs online?",
                    "answer": f"Shopping locally in {city} with {self.brand_name} offers immediate availability, personal service, and local expertise. You can see, touch, and test products before buying, plus get instant expert advice from our {city} team."
                },
                {
                    "question": f"Are there any special offers for {city} residents?",
                    "answer": f"Yes, {self.brand_name} offers exclusive deals for {city} residents, including local discounts and special promotions. We also have loyalty programs and seasonal offers that are perfect for {city} shoppers."
                },
                {
                    "question": f"Can I get same-day service in {city}?",
                    "answer": f"Absolutely! {self.brand_name} provides same-day service throughout {city}. Our local team ensures fast turnaround times and can often accommodate urgent requests from {city} customers."
                },
                {
                    "question": f"What makes {self.brand_name} different from other options in {city}?",
                    "answer": f"{self.brand_name} stands out in {city} with our local expertise, personalized service, and deep understanding of {city}'s unique needs. We're not just another chain - we're part of the {city} community."
                },
                {
                    "question": f"Do you offer delivery throughout {city}?",
                    "answer": f"Yes, {self.brand_name} offers comprehensive delivery services throughout {city}, including to areas near {landmarks}. We ensure fast, reliable delivery with tracking and customer support from our {city} team."
                }
            ]
    
    def _generate_images(self) -> List[Dict[str, str]]:
        """Generate image suggestions (≥2) with localized alt text"""
        if self.language.startswith('lt'):
            return [
                {
                    "alt": f"{self.target_keyword} vadovas Vilniuje",
                    "src": f"/images/{self.target_keyword.lower().replace(' ', '-')}-overview.jpg",
                    "caption": f"Išsamus {self.target_keyword} vadovas"
                },
                {
                    "alt": f"{self.brand_name} kvepalų parduotuvė Vilniuje",
                    "src": f"/images/{self.brand_name.lower().replace(' ', '-')}-services.jpg",
                    "caption": f"{self.brand_name} profesionalūs kvepalų paslaugos Vilniuje"
                }
            ]
        else:
            return [
                {
                    "alt": f"{self.target_keyword} overview image",
                    "src": f"/images/{self.target_keyword.lower().replace(' ', '-')}-overview.jpg",
                    "caption": f"Comprehensive guide to {self.target_keyword}"
                },
                {
                    "alt": f"{self.brand_name} {self.target_keyword} services",
                    "src": f"/images/{self.brand_name.lower().replace(' ', '-')}-services.jpg",
                    "caption": f"{self.brand_name} professional {self.target_keyword} services"
                }
            ]
    
    def _generate_internal_links(self) -> List[Dict[str, str]]:
        """Generate internal links (≥2) with localized anchor text"""
        if self.language.startswith('lt'):
            return [
                {
                    "text": f"Sužinokite daugiau apie {self.brand_name} paslaugas",
                    "url": "/services",
                    "anchor": "mūsų-paslaugos"
                },
                {
                    "text": f"Susisiekite su {self.brand_name} konsultacijai",
                    "url": "/contact",
                    "anchor": "susisiekite-su-mumis"
                }
            ]
        else:
            return [
                {
                    "text": f"Learn more about {self.brand_name} services",
                    "url": "/services",
                    "anchor": "our-services"
                },
                {
                    "text": f"Contact {self.brand_name} for consultation",
                    "url": "/contact",
                    "anchor": "get-in-touch"
                }
            ]
    
    def _generate_aeo_content_text(self, sections: List[Dict], faqs: List[Dict]) -> str:
        """Generate AEO-optimized content text (1000-1200 words)"""
        
        localized = self._get_localized_content()
        
        content = f"# {self.target_keyword}: Complete Guide\n\n"
        
        # Start with local problem statement, not generic greeting
        if self.language.startswith('lt'):
            content += f"{localized['intro_prefix']}. {self.brand_name} teikia ekspertų patarimus, kurie padės rasti geriausias kvepalų pirkimo galimybes Vilniuje."
        else:
            content += f"{localized['intro_prefix']}. {self.brand_name} provides expert guidance to help you find the best options."
        
        # Add city mention for AEO (light GEO tie-in)
        if self.site_city:
            if self.language.startswith('lt'):
                content += f" Šiame vadove aptarsime geriausias {self.target_keyword} galimybes {self.site_city} ir apylinkėse.\n\n"
            else:
                content += f" This guide covers the best {self.target_keyword} options in {self.site_city} and surrounding areas.\n\n"
        else:
            content += "\n\n"
        
        # Add sections
        for section in sections:
            content += f"## {section['heading']}\n\n"
            content += f"{section['content']}\n\n"
        
        # Add FAQ section
        content += f"## {localized['faq_heading']}\n\n"
        for faq in faqs:
            content += f"### {faq['question']}\n\n"
            content += f"{faq['answer']}\n\n"
        
        content += f"## {localized['conclusion']}\n\n"
        content += f"Suprasti {self.target_keyword} yra labai svarbu priimant pagrįstus sprendimus. {self.brand_name} yra jūsų patikimas partneris, teikiantis ekspertų patarimus ir profesionalias paslaugas.\n\n"
        
        # Ensure minimum word count (1000-1200 for AEO)
        content = self._ensure_word_count(content, 1000)
        
        return content
    
    def _generate_geo_content_text(self, sections: List[Dict], faqs: List[Dict]) -> str:
        """Generate GEO-optimized content text (1200-1500 words) in target language"""
        
        localized = self._get_localized_content()
        city = self._get_city_name()
        
        if self.language.startswith('lt'):
            content = f"# {self.target_keyword} {city}: Vietinis vadovas\n\n"
            content += f"Atraskite geriausias {self.target_keyword} galimybes {city}. {self.brand_name} teikia vietinę ekspertizę ir įžvalgas {city} gyventojams.\n\n"
        else:
            content = f"# {self.target_keyword} in {city}: Local Guide\n\n"
            content += f"Discover the best {self.target_keyword} options in {city}. {self.brand_name} provides local expertise and insights for {city} residents.\n\n"
        
        # Add sections
        for section in sections:
            content += f"## {section['heading']}\n\n"
            content += f"{section['content']}\n\n"
        
        # Add FAQ section
        content += f"## {localized['faq_heading']}\n\n"
        for faq in faqs:
            content += f"### {faq['question']}\n\n"
            content += f"{faq['answer']}\n\n"
        
        # Add conclusion
        content += f"## {localized['conclusion']}\n\n"
        if self.language.startswith('lt'):
            content += f"Išnaudokite {self.target_keyword} {city} su mūsų vietiniu vadovu. {self.brand_name} yra jūsų patikimas partneris {city}.\n\n"
        else:
            content += f"Make the most of {self.target_keyword} in {city} with our local guide. {self.brand_name} is your trusted partner in {city}.\n\n"
        
        # Ensure minimum word count (1200-1500 for GEO)
        content = self._ensure_word_count(content, 1200)
        
        return content
    
    def _generate_aeo_json_ld(self, faqs: List[Dict]) -> Dict[str, Any]:
        """Generate AEO JSON-LD schema"""
        return {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": f"{self.target_keyword}: Complete Guide",
            "description": f"Comprehensive guide to {self.target_keyword} by {self.brand_name}",
            "author": {
                "@type": "Organization",
                "name": self.brand_name
            },
            "publisher": {
                "@type": "Organization",
                "name": self.brand_name
            },
            "datePublished": datetime.now().isoformat(),
            "mainEntity": {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": faq["question"],
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": faq["answer"]
                        }
                    } for faq in faqs
                ]
            }
        }
    
    def _generate_geo_json_ld(self, faqs: List[Dict], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate GEO JSON-LD schema with LocalBusiness"""
        
        # Base article schema
        article_schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": f"{self.target_keyword} in {self._get_city_name()}: Local Guide",
            "description": f"Local guide to {self.target_keyword} in {self._get_city_name()} by {self.brand_name}",
            "author": {
                "@type": "Organization",
                "name": self.brand_name
            },
            "publisher": {
                "@type": "Organization",
                "name": self.brand_name
            },
            "datePublished": datetime.now().isoformat(),
            "mainEntity": {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": faq["question"],
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": faq["answer"]
                        }
                    } for faq in faqs
                ]
            }
        }
        
        # LocalBusiness schema (with empty fields if no data)
        local_business = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": self.brand_name,
            "description": f"{self.brand_name} provides {self.target_keyword} services",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": self._get_city_name(),
                "addressCountry": "LT"  # Default to Lithuania
            }
        }
        
        return {
            "article": article_schema,
            "local_business": local_business
        }
    
    def _get_city_name(self) -> str:
        """Get city name from context or detect from target keyword"""
        if self.context and 'location' in self.context:
            return self.context['location']
        
        # Try to detect city from target keyword
        target_lower = self.target_keyword.lower()
        if 'kaune' in target_lower or 'kaunas' in target_lower:
            return "Kaunas"
        elif 'vilniuje' in target_lower or 'vilnius' in target_lower:
            return "Vilnius"
        elif 'klaipėdoje' in target_lower or 'klaipeda' in target_lower:
            return "Klaipėda"
        elif 'šiauliuose' in target_lower or 'siauliai' in target_lower:
            return "Šiauliai"
        elif 'panevėžyje' in target_lower or 'panevezys' in target_lower:
            return "Panevėžys"
        
        return "Vilnius"  # Default fallback
    
    def _get_landmarks(self) -> str:
        """Get local landmarks for GEO content based on city"""
        city = self._get_city_name()
        if city == "Kaunas":
            return "Akropolis, Mega, Laisvės alėja"
        elif city == "Vilnius":
            return "Akropolis, Panorama, Gedimino pr."
        elif city == "Klaipėda":
            return "Akropolis, Švyturys, Tiltų g."
        elif city == "Šiauliai":
            return "Saulės miestas, Tilžės g., Vilniaus g."
        elif city == "Panevėžys":
            return "Akropolis, Respublikos g., Smėlynės g."
        else:
            return "Akropolis, Panorama, Gedimino pr."  # Default
    
    def _get_localized_content(self) -> Dict[str, str]:
        """Get localized content based on language with proper Lithuanian examples"""
        if self.language.startswith('lt'):
            return {
                'faq_heading': 'Dažniausiai užduodami klausimai',
                'conclusion': 'Išvados',
                'intro_prefix': 'Vilniaus pirkėjai dažnai klausia, kur geriausia įsigyti originalius kvepalus',
                'benefits_heading': 'Pagrindiniai privalumai',
                'comparison_heading': 'Palyginimas',
                'tips_heading': 'Patarimai ir rekomendacijos',
                'quality_heading': 'Kokybės vertinimas',
                'value_heading': 'Vertės palyginimas',
                'expert_heading': 'Ekspertų rekomendacijos'
            }
        else:  # Default to English
            return {
                'faq_heading': 'Frequently Asked Questions',
                'conclusion': 'Conclusion',
                'intro_prefix': 'Local buyers often ask where to find authentic products',
                'benefits_heading': 'Key Benefits',
                'comparison_heading': 'Comparison',
                'tips_heading': 'Tips and Recommendations',
                'quality_heading': 'Quality Assessment',
                'value_heading': 'Value Comparison',
                'expert_heading': 'Expert Recommendations'
            }
    
    def _ensure_word_count(self, content: str, min_words: int) -> str:
        """Ensure content meets minimum word count by expanding with examples and tips"""
        word_count = len(content.split())
        if word_count < min_words:
            # Add expansion content in target language
            if self.language.startswith('lt'):
                expansion = f"""
                
                ## Papildomi įžvalgos ir patarimai

                Apsvarstydami savo variantus, svarbu įvertinti kelis pagrindinius veiksnius:

                **Kokybės vertinimas**: Ieškokite kokybės rodiklių, tokių kaip medžiagos, meistriškumas ir prekės ženklo reputacija. {self.brand_name} palaiko aukštus standartus visuose mūsų pasiūlymuose.

                **Vertės palyginimas**: Palyginkite ne tik kainą, bet ir vertę - ką gaunate už savo investiciją. Apsvarstykite ilgalaikius privalumus, patvarumą ir bendrą pasitenkinimą.

                **Ekspertų rekomendacijos**: Mūsų {self.brand_name} komanda turi didelę patirtį ir gali suteikti individualizuotas rekomendacijas, atsižvelgdama į jūsų specifinius poreikius ir pageidavimus.

                **Klientų atsiliepimai**: Skaitykite autentiškus atsiliepimus iš kitų klientų, kurie priėmė panašius sprendimus. Jų patirtis gali suteikti vertingų įžvalgų.

                **Išbandymas ir testavimas**: Kada tik įmanoma, išbandykite ar paragaukite prieš priimdami galutinį sprendimą. {self.brand_name} siūlo įvairius būdus išbandyti mūsų produktus prieš pirkimą.

                **Po pardavimo palaikymas**: Apsvarstykite palaikymą ir paslaugas, kurias gausite po pirkimo. {self.brand_name} teikia išsamų klientų aptarnavimą ir palaikymą.

                **Ilgalaikiai svarstymai**: Pagalvokite, kaip jūsų pasirinkimas tarnaus jums laikui bėgant, ne tik iš karto. Kokybė ir patvarumas dažnai suteikia geresnę ilgalaikę vertę.

                **Asmeniniai pageidavimai**: Jūsų individualūs poreikiai, stilius ir pageidavimai turėtų vadovauti jūsų sprendimui. {self.brand_name} siūlo įvairius variantus, tinkančius skirtingiems skoniams ir reikalavimams.

                **Biudžeto planavimas**: Nustatykite realų biudžetą ir laikykitės jo, bet taip pat apsvarstykite kokybės investavimo vertę. Kartais šiek tiek daugiau išleisti iš karto ilgainiui sutaupo pinigų.

                **Tyrimai ir švietimas**: Skirkite laiko išmokti apie savo variantus. {self.brand_name} teikia švietimo išteklius ir ekspertų vadovavimą, kuris padės priimti pagrįstus sprendimus.
                """
            else:  # English fallback
                expansion = f"""
                
                ## Additional Insights and Tips

                When considering your options, it's important to evaluate several key factors:

                **Quality Assessment**: Look for indicators of quality such as materials, craftsmanship, and brand reputation. {self.brand_name} maintains high standards across all our offerings.

                **Value Comparison**: Compare not just price, but value - what you get for your investment. Consider long-term benefits, durability, and overall satisfaction.

                **Expert Recommendations**: Our team at {self.brand_name} has extensive experience and can provide personalized recommendations based on your specific needs and preferences.

                **Customer Reviews**: Read authentic reviews from other customers who have made similar choices. Their experiences can provide valuable insights.

                **Trial and Testing**: Whenever possible, test or sample before making a final decision. {self.brand_name} offers various ways to experience our products before purchase.

                **After-Sales Support**: Consider the support and service you'll receive after your purchase. {self.brand_name} provides comprehensive customer service and support.

                **Long-term Considerations**: Think about how your choice will serve you over time, not just immediately. Quality and durability often provide better long-term value.

                **Personal Preferences**: Your individual needs, style, and preferences should guide your decision. {self.brand_name} offers diverse options to suit different tastes and requirements.

                **Budget Planning**: Set a realistic budget and stick to it, but also consider the value of investing in quality. Sometimes spending a bit more upfront saves money long-term.

                **Research and Education**: Take time to learn about your options. {self.brand_name} provides educational resources and expert guidance to help you make informed decisions.
                """
            content += expansion
        return content
