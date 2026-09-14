"""
Suite de Pruebas Automatizadas de Calidad y Cumplimiento de Reglas Estrictas
Valida:
1. Regla del tiempo crítica (inversión si es descendente, pasado -> presente).
2. Rendimientos simples mensuales y exclusión de IPC.
3. Cálculos estrictamente mensuales (no anualizar).
4. Optimización de Markowitz (restricciones sum(w)=1, w>=0, sigma_p <= 0.07).
5. Simulación de Monte Carlo (1,000 carteras válidas).
6. Agente Cuantitativo Autónomo (diagnósticos y respuestas técnicas).
7. Centro de Auditoría de Calidad y Limpieza de Errores.
8. Generación de informes en Word (.docx) y PDF (.pdf).
9. Conexión a API bursátil de mercado en vivo.
"""

import os
import unittest
import numpy as np
import pandas as pd
from docx import Document

import optimizer
import agent
import word_exporter
import pdf_exporter
import api_fetcher


class TestMarkowitzPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.excel_file = "Histórico_Acciones.xlsx"
        if not os.path.exists(cls.excel_file):
            raise FileNotFoundError(f"Archivo base '{cls.excel_file}' no encontrado.")
        cls.prep = optimizer.load_and_preprocess_data(cls.excel_file)
        cls.stats = optimizer.compute_monthly_statistics(cls.prep["stock_returns"])
        cls.opt = optimizer.optimize_markowitz_max_return(cls.prep["stock_returns"], max_std=0.07)
        cls.mc = optimizer.run_monte_carlo_simulation(cls.prep["stock_returns"], num_portfolios=1000)
        cls.bench = optimizer.calculate_benchmark_metrics(cls.opt["portfolio_returns"], cls.prep["ipc_returns"])
        cls.ag = agent.QuantitativePortfolioAgent()
        cls.agent_rep = cls.ag.generate_autonomous_report(cls.prep, cls.stats, cls.opt, cls.mc, cls.bench)

    def test_chronological_order(self):
        """Regla 1: Orden estrictamente pasado -> presente."""
        dates = self.prep["dates"]
        self.assertTrue((dates.diff().dropna() > pd.Timedelta(0)).all())
        self.assertLess(self.prep["start_date"], self.prep["end_date"])

    def test_ipc_exclusion(self):
        """Regla 1: Exclusión del IPC de las acciones a optimizar."""
        self.assertNotIn("IPC", self.prep["stock_cols"])
        self.assertIn("IPC", str(self.prep["ipc_col"]))

    def test_monthly_statistics_not_annualized(self):
        """Regla 2: Parámetros estrictamente mensuales sin anualizar."""
        mean_ret = self.stats["mean_returns"]
        self.assertTrue((mean_ret > -0.10).all() and (mean_ret < 0.10).all())
        std_ret = self.stats["std_devs"]
        self.assertTrue((std_ret > 0.01).all() and (std_ret < 0.25).all())

    def test_markowitz_constraints(self):
        """Regla 3: Restricciones de Markowitz cumplidas al 100%."""
        weights = self.opt["weights"]
        self.assertAlmostEqual(np.sum(weights), 1.0, places=5)
        self.assertTrue((weights >= -1e-6).all())
        self.assertLessEqual(self.opt["volatility"], 0.0701)
        self.assertGreater(self.opt["expected_return"], 0.0)

    def test_monte_carlo_properties(self):
        """Regla 4: Simulación de 1,000 carteras aleatorias válidas."""
        sim_df = self.mc["simulation_df"]
        self.assertEqual(len(sim_df), 1000)
        self.assertTrue((sim_df["Volatilidad Mensual"] > 0).all())
        all_w = self.mc["all_weights"]
        self.assertTrue(np.allclose(np.sum(all_w, axis=1), 1.0, atol=1e-5))

    def test_agent_advanced_qa(self):
        """Regla del Agente Autónomo: Respuestas constructivas y detalladas."""
        context = {
            "opt_ret": self.opt["expected_return"],
            "opt_vol": self.opt["volatility"],
            "target_std": 0.07,
            "weights_summary": "PEÑOLES: 37.2%, ASUR: 34.0%",
        }
        ans = self.ag.ask_agent("¿Por qué ciertos activos tienen peso 0%?", context)
        self.assertIn("Diagnóstico", ans)
        self.assertIn("Markowitz", ans)
        self.assertIn("Comité de Inversión", ans)

    def test_data_audit_log(self):
        """Regla del Centro de Auditoría: Identificación de anomalías y limpieza."""
        self.assertIn("audit_events", self.prep)
        self.assertGreater(len(self.prep["audit_events"]), 3)
        self.assertIn("cleaned_export_df", self.prep)

    def test_word_and_pdf_export(self):
        """Regla de exportación funcional a Word (.docx) y PDF (.pdf)."""
        test_docx = "test_out.docx"
        test_pdf = "test_out.pdf"
        
        # Word
        word_exporter.generate_word_report(
            self.prep, self.stats, self.opt, self.mc, self.bench, self.agent_rep, output_path=test_docx
        )
        self.assertTrue(os.path.exists(test_docx))
        doc = Document(test_docx)
        self.assertGreater(len(doc.paragraphs), 10)
        doc_texts = [p.text for p in doc.paragraphs]
        self.assertTrue(any("TRABAJO" in t for t in doc_texts))
        self.assertTrue(any("Portafolio diversificado usando rendimientos reales" in t for t in doc_texts))
        self.assertTrue(any("Cristian Andres Cordoba Gonzalez" in t for t in doc_texts))
        self.assertTrue(any("Daniel Vázquez Cotera" in t for t in doc_texts))
        self.assertTrue(any("Broward International University" in t for t in doc_texts))
        os.remove(test_docx)

        # PDF
        pdf_exporter.generate_pdf_report(
            self.prep, self.stats, self.opt, self.mc, self.bench, self.agent_rep, output_path=test_pdf
        )
        self.assertTrue(os.path.exists(test_pdf))
        self.assertGreater(os.path.getsize(test_pdf), 10000)
        os.remove(test_pdf)

    def test_adaptive_risk_on_infeasible_constraint(self):
        """Regla de Autonomía Adaptativa: Si max_std < min_possible_std, no falla y adapta."""
        cg_file = "/Users/cristinancordoba/Desktop/Maestria/SM26_BIA6042_Financial Management with Artificial Intelligence MBA/Historico_Acciones CG.xlsx"
        if os.path.exists(cg_file):
            # Probar explícitamente la hoja report (donde min_possible_std es 7.25% > 7.00%)
            prep_cg = optimizer.load_and_preprocess_data(cg_file, sheet_name="report")
            opt_cg = optimizer.optimize_markowitz_max_return(prep_cg["stock_returns"], max_std=0.07, adaptive_risk=True)
            self.assertTrue(opt_cg["adapted_risk"])
            self.assertGreater(opt_cg["target_max_std"], 0.07)
            self.assertAlmostEqual(opt_cg["volatility"], opt_cg["min_possible_std"], places=4)
            self.assertAlmostEqual(np.sum(opt_cg["weights"]), 1.0, places=5)
            self.assertTrue((opt_cg["weights"] >= -1e-6).all())

            # Verificar que el agente documenta la decisión
            rep_cg = self.ag.generate_autonomous_report(prep_cg, optimizer.compute_monthly_statistics(prep_cg["stock_returns"]), opt_cg, self.mc, None)
            self.assertIn("Decisión Cuantitativa Autónoma", rep_cg["executive_summary"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
