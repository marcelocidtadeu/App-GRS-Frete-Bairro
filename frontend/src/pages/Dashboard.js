import { useState, useEffect } from "react";
import axios from "axios";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Settings, FileSpreadsheet, MapPin, History } from "lucide-react";
import ConfigModal from "@/components/ConfigModal";
import CotacaoTab from "@/components/CotacaoTab";
import CepTab from "@/components/CepTab";
import HistoryTable from "@/components/HistoryTable";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard() {
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [config, setConfig] = useState(null);
  const [activeTab, setActiveTab] = useState("cotacao");
  const [refreshHistory, setRefreshHistory] = useState(0);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await axios.get(`${API}/config/intelipost`);
      setConfig(response.data);
    } catch (error) {
      console.error("Erro ao carregar configuração:", error);
    }
  };

  const handleConfigSaved = () => {
    loadConfig();
    toast.success("Configuração salva com sucesso!");
    setShowConfigModal(false);
  };

  const handleProcessingComplete = () => {
    setRefreshHistory(prev => prev + 1);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">Processador de Planilhas Excel</h1>
              <p className="text-sm text-slate-600 mt-1">Cotação de Frete e Busca de Endereços</p>
            </div>
            <Button
              data-testid="config-button"
              onClick={() => setShowConfigModal(true)}
              variant="outline"
              className="flex items-center gap-2 hover:bg-slate-50"
            >
              <Settings className="h-4 w-4" />
              Configurações
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full max-w-md mx-auto grid-cols-3 bg-white border border-slate-200 p-1 rounded-lg shadow-sm">
            <TabsTrigger
              data-testid="tab-cotacao"
              value="cotacao"
              className="flex items-center gap-2 data-[state=active]:bg-blue-600 data-[state=active]:text-white transition-all"
            >
              <FileSpreadsheet className="h-4 w-4" />
              Cotação Intelipost
            </TabsTrigger>
            <TabsTrigger
              data-testid="tab-cep"
              value="cep"
              className="flex items-center gap-2 data-[state=active]:bg-blue-600 data-[state=active]:text-white transition-all"
            >
              <MapPin className="h-4 w-4" />
              Busca CEP
            </TabsTrigger>
            <TabsTrigger
              data-testid="tab-history"
              value="historico"
              className="flex items-center gap-2 data-[state=active]:bg-blue-600 data-[state=active]:text-white transition-all"
            >
              <History className="h-4 w-4" />
              Histórico
            </TabsTrigger>
          </TabsList>

          <TabsContent value="cotacao" className="animate-in fade-in zoom-in-95 duration-300">
            <CotacaoTab config={config} onComplete={handleProcessingComplete} />
          </TabsContent>

          <TabsContent value="cep" className="animate-in fade-in zoom-in-95 duration-300">
            <CepTab onComplete={handleProcessingComplete} />
          </TabsContent>

          <TabsContent value="historico" className="animate-in fade-in zoom-in-95 duration-300">
            <Card className="bg-white border-slate-200 rounded-xl shadow-sm">
              <CardHeader>
                <CardTitle className="text-slate-900">Histórico de Processamentos</CardTitle>
                <CardDescription>Visualize todos os processamentos anteriores</CardDescription>
              </CardHeader>
              <CardContent>
                <HistoryTable refreshTrigger={refreshHistory} />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* Config Modal */}
      <ConfigModal
        open={showConfigModal}
        onClose={() => setShowConfigModal(false)}
        onSave={handleConfigSaved}
        currentConfig={config}
      />
    </div>
  );
}